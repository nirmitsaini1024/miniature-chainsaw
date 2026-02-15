import os
import uuid
import asyncio
from typing import Dict, Optional
from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    FloodWaitError
)
from telethon.tl.types import User


class TelegramService:
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        
        # In-memory storage for active clients and pending codes
        self.clients: Dict[str, TelegramClient] = {}
        self.pending_sessions: Dict[str, Dict] = {}  # session_id -> {phone, phone_code_hash, api_id, api_hash}
        self.authenticated_sessions: Dict[str, str] = {}  # token -> session_id
        self.session_credentials: Dict[str, Dict] = {}  # session_id -> {api_id, api_hash}
        
    def _get_session_path(self, session_id: str) -> str:
        """Get the session file path for a given session ID."""
        return os.path.join(self.sessions_dir, f"{session_id}.session")
    
    async def send_code(self, phone: str, api_id: int, api_hash: str) -> Dict:
        """
        Send OTP code to the phone number.
        Returns session_id and phone_code_hash.
        """
        try:
            session_id = str(uuid.uuid4())
            session_path = self._get_session_path(session_id)
            
            # Store API credentials for this session
            self.session_credentials[session_id] = {
                "api_id": api_id,
                "api_hash": api_hash
            }
            
            # Create a new client for this session with user-provided credentials
            client = TelegramClient(session_path, api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                # Send code request
                result = await client.send_code_request(phone)
                phone_code_hash = result.phone_code_hash
                
                # Store pending session info
                self.pending_sessions[session_id] = {
                    "phone": phone,
                    "phone_code_hash": phone_code_hash,
                    "client": client,
                    "api_id": api_id,
                    "api_hash": api_hash
                }
                
                # Store client
                self.clients[session_id] = client
                
                return {
                    "session_id": session_id,
                    "status": "code_sent",
                    "message": "Code sent successfully"
                }
            else:
                # Already authorized, generate token
                await client.disconnect()
                token = str(uuid.uuid4())
                self.authenticated_sessions[token] = session_id
                return {
                    "session_id": session_id,
                    "status": "already_authorized",
                    "token": token,
                    "message": "Already authenticated"
                }
                
        except PhoneNumberInvalidError:
            raise ValueError("Invalid phone number")
        except FloodWaitError as e:
            raise ValueError(f"Rate limited. Please wait {e.seconds} seconds")
        except Exception as e:
            raise ValueError(f"Failed to send code: {str(e)}")
    
    async def verify_code(
        self, 
        session_id: str, 
        code: str, 
        password: Optional[str] = None
    ) -> Dict:
        """
        Verify OTP code and complete authentication.
        Returns token and user info.
        """
        if session_id not in self.pending_sessions:
            raise ValueError("Invalid or expired session")
        
        session_info = self.pending_sessions[session_id]
        client = session_info["client"]
        phone = session_info["phone"]
        
        try:
            # Ensure client is connected
            if not client.is_connected():
                await client.connect()
            
            # Verify code
            try:
                user = await client.sign_in(phone, code, phone_code_hash=session_info["phone_code_hash"])
            except SessionPasswordNeededError:
                if not password:
                    raise ValueError("2FA password required")
                user = await client.sign_in(password=password)
            
            # Get user info
            me = await client.get_me()
            user_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone
            }
            
            # Generate token
            token = str(uuid.uuid4())
            self.authenticated_sessions[token] = session_id
            
            # Remove from pending
            del self.pending_sessions[session_id]
            
            return {
                "token": token,
                "user_info": user_info,
                "status": "authenticated"
            }
            
        except PhoneCodeInvalidError:
            raise ValueError("Invalid code")
        except PhoneCodeExpiredError:
            raise ValueError("Code expired. Please request a new code")
        except Exception as e:
            raise ValueError(f"Verification failed: {str(e)}")
    
    def get_client(self, token: str) -> Optional[TelegramClient]:
        """Get authenticated Telegram client by token."""
        if token not in self.authenticated_sessions:
            return None
        
        session_id = self.authenticated_sessions[token]
        if session_id not in self.clients:
            # Reconnect client with stored credentials
            session_path = self._get_session_path(session_id)
            if session_id not in self.session_credentials:
                return None
            creds = self.session_credentials[session_id]
            client = TelegramClient(session_path, creds["api_id"], creds["api_hash"])
            self.clients[session_id] = client
        
        return self.clients[session_id]
    
    async def ensure_connected(self, client: TelegramClient):
        """Ensure client is connected and authorized."""
        if not client.is_connected():
            await client.connect()
        
        if not await client.is_user_authorized():
            raise ValueError("Session expired. Please re-authenticate")

