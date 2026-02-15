import os
import uuid
import asyncio
from typing import Dict, Optional, List
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from telethon.errors import ChannelInvalidError, ChannelPrivateError
import re


class DownloadState:
    def __init__(self, download_id: str, channel_id: int, session_id: str):
        self.download_id = download_id
        self.channel_id = channel_id
        self.session_id = session_id
        self.status = "pending"
        self.progress = 0.0
        self.total_files = 0
        self.downloaded_files = 0
        self.files: List[Dict] = []
        self.current_file: Optional[str] = None
        self.error: Optional[str] = None
        self.download_dir: str = ""
        self.last_message_id: Optional[int] = None


class DownloadService:
    def __init__(self, downloads_dir: str = "downloads"):
        self.downloads_dir = downloads_dir
        os.makedirs(downloads_dir, exist_ok=True)
        
        # In-memory storage for download states
        self.downloads: Dict[str, DownloadState] = {}
    
    def parse_channel_input(self, channel_input: str) -> Dict:
        """
        Parse channel input to extract channel identifier.
        Supports:
        - @channelname
        - https://t.me/channelname
        - https://t.me/c/CHANNEL_ID/MESSAGE_ID
        - https://t.me/+HASH (invite link)
        - Channel ID (numeric)
        """
        channel_input = channel_input.strip()
        
        # Check if it's an invite link (t.me/+hash)
        match = re.search(r't\.me/\+([a-zA-Z0-9_-]+)', channel_input)
        if match:
            invite_hash = match.group(1)
            return {"type": "invite", "value": invite_hash, "original": channel_input}
        
        # Check if it's a numeric ID
        if channel_input.lstrip('-').isdigit():
            try:
                channel_id = int(channel_input)
                # For supergroups, try supergroup format first
                if channel_id > 0 and not channel_input.startswith('-100'):
                    return {"type": "id", "value": channel_id, "original": channel_input, "try_supergroup": True}
                return {"type": "id", "value": channel_id, "original": channel_input}
            except ValueError:
                pass
        
        # Check if it's a t.me link with channel ID
        match = re.search(r't\.me/c/(\d+)', channel_input)
        if match:
            channel_id = int(match.group(1))
            # For supergroups, convert to -100XXXXXXXXXX format
            return {"type": "id", "value": channel_id, "original": channel_input, "try_supergroup": True}
        
        # Check if it's a t.me link with username
        match = re.search(r't\.me/([a-zA-Z0-9_]+)', channel_input)
        if match:
            username = match.group(1)
            return {"type": "username", "value": username, "original": channel_input}
        
        # Check if it's @username
        if channel_input.startswith('@'):
            username = channel_input[1:]
            return {"type": "username", "value": username, "original": channel_input}
        
        # Assume it's a username without @
        return {"type": "username", "value": channel_input, "original": channel_input}
    
    async def resolve_channel_id(
        self, 
        client: TelegramClient, 
        channel_info: Dict
    ) -> int:
        """Resolve channel username, invite link, or ID to channel ID."""
        # Handle invite links
        if channel_info["type"] == "invite":
            from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
            from telethon.tl.types import ChatInviteAlready, ChatInvite
            
            invite_hash = channel_info["value"]
            try:
                # First check the invite
                invite = await client(CheckChatInviteRequest(invite_hash))
                
                # If already a member, get the chat ID directly
                if isinstance(invite, ChatInviteAlready):
                    return invite.chat.id
                
                # If it's an invite that needs to be imported
                if isinstance(invite, ChatInvite):
                    # Import/join the channel
                    result = await client(ImportChatInviteRequest(invite_hash))
                    
                    # Extract channel ID from the result
                    # The updates contain information about the joined chat
                    for update in result.updates:
                        # Check for channel updates (UpdateNewMessage with channel peer)
                        if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
                            peer = update.message.peer_id
                            if hasattr(peer, 'channel_id'):
                                # Convert to supergroup format
                                return -1000000000000 - peer.channel_id
                        # Check for chat updates
                        if hasattr(update, 'chat') and hasattr(update.chat, 'id'):
                            chat_id = update.chat.id
                            return chat_id
                    
                    # Fallback: try to get from the invite's channel info if available
                    # Some invites have channel information
                    raise ValueError("Joined channel but could not extract ID. The channel should now be accessible.")
                
                raise ValueError("Unknown invite type")
            except Exception as e:
                error_msg = str(e)
                if "INVITE_HASH_EXPIRED" in error_msg or "expired" in error_msg.lower():
                    raise ValueError("Invite link has expired")
                raise ValueError(f"Failed to resolve invite link: {error_msg}")
        
        # Handle numeric IDs
        if channel_info["type"] == "id":
            channel_id = channel_info["value"]
            
            # If it's a positive ID, try supergroup format first
            if channel_id > 0:
                # Try supergroup format first (-100XXXXXXXXXX)
                channel_str = str(channel_id)
                supergroup_id = int(f"-100{channel_str}")
                try:
                    entity = await client.get_entity(supergroup_id)
                    return entity.id
                except:
                    # If supergroup format fails, try as regular channel ID
                    try:
                        entity = await client.get_entity(channel_id)
                        return entity.id
                    except Exception as e:
                        # If both fail, try the supergroup format one more time with different approach
                        raise ValueError(f"Failed to resolve channel ID {channel_id}. Try using the full invite link or channel username instead.")
            elif channel_id < 0:
                # Already in correct format
                try:
                    entity = await client.get_entity(channel_id)
                    return entity.id
                except Exception as e:
                    raise ValueError(f"Failed to resolve channel ID {channel_id}: {str(e)}")
        
        # Resolve username to entity
        try:
            entity = await client.get_entity(channel_info["value"])
            return entity.id
        except Exception as e:
            raise ValueError(f"Failed to resolve channel: {str(e)}")
    
    def _get_download_dir(self, session_id: str, channel_id: int) -> str:
        """Get download directory for a session and channel."""
        dir_path = os.path.join(self.downloads_dir, session_id, str(abs(channel_id)))
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    
    def _get_progress_file(self, download_dir: str) -> str:
        """Get progress file path."""
        return os.path.join(download_dir, "last_message_id.txt")
    
    def _read_last_message_id(self, download_dir: str) -> Optional[int]:
        """Read the last downloaded message ID."""
        progress_file = self._get_progress_file(download_dir)
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return int(content)
            except (ValueError, IOError):
                pass
        return None
    
    def _save_last_message_id(self, download_dir: str, message_id: int):
        """Save the last downloaded message ID."""
        progress_file = self._get_progress_file(download_dir)
        try:
            with open(progress_file, 'w') as f:
                f.write(str(message_id))
        except IOError:
            pass
    
    def _has_media(self, message) -> bool:
        """Check if message has downloadable media."""
        return (
            message.media and (
                isinstance(message.media, MessageMediaDocument) or
                isinstance(message.media, MessageMediaPhoto)
            )
        )
    
    async def start_download(
        self,
        client: TelegramClient,
        channel_id: int,
        session_id: str
    ) -> str:
        """Start downloading files from a channel."""
        download_id = str(uuid.uuid4())
        download_dir = self._get_download_dir(session_id, channel_id)
        
        # Create download state
        state = DownloadState(download_id, channel_id, session_id)
        state.download_dir = download_dir
        state.status = "in_progress"
        self.downloads[download_id] = state
        
        # Start download in background
        asyncio.create_task(self._download_files(client, state))
        
        return download_id
    
    async def _download_files(self, client: TelegramClient, state: DownloadState):
        """Download files from channel (runs in background)."""
        try:
            # Ensure client is connected
            if not client.is_connected():
                await client.connect()
            
            # Read resume point
            last_downloaded = self._read_last_message_id(state.download_dir)
            state.last_message_id = last_downloaded
            
            if last_downloaded is not None:
                resume_from = last_downloaded
            else:
                resume_from = 0
            
            # Collect messages with media
            messages = []
            async for message in client.iter_messages(
                state.channel_id,
                min_id=resume_from,
                reverse=True
            ):
                if self._has_media(message):
                    messages.append(message)
            
            state.total_files = len(messages)
            
            if state.total_files == 0:
                state.status = "completed"
                state.progress = 100.0
                return
            
            # Download files sequentially
            for idx, message in enumerate(messages, 1):
                try:
                    state.current_file = f"Message ID {message.id}"
                    filepath = await message.download_media(file=state.download_dir)
                    
                    if filepath:
                        filename = os.path.basename(filepath)
                        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                        
                        file_info = {
                            "filename": filename,
                            "size": file_size,
                            "path": filepath,
                            "download_url": f"/api/download/files/{state.download_id}/{filename}"
                        }
                        state.files.append(file_info)
                        state.downloaded_files += 1
                        
                        # Save progress
                        self._save_last_message_id(state.download_dir, message.id)
                        state.last_message_id = message.id
                    
                    # Update progress
                    state.progress = (state.downloaded_files / state.total_files) * 100
                    
                except Exception as e:
                    # Continue with next file on error
                    print(f"Error downloading message {message.id}: {e}")
                    continue
            
            state.status = "completed"
            state.progress = 100.0
            state.current_file = None
            
        except ChannelInvalidError:
            state.status = "failed"
            state.error = "Invalid channel"
        except ChannelPrivateError:
            state.status = "failed"
            state.error = "Channel is private or access denied"
        except Exception as e:
            state.status = "failed"
            state.error = str(e)
    
    def get_download_status(self, download_id: str) -> Optional[DownloadState]:
        """Get download status by ID."""
        return self.downloads.get(download_id)
    
    def get_download_file_path(self, download_id: str, filename: str) -> Optional[str]:
        """Get file path for download."""
        state = self.downloads.get(download_id)
        if not state:
            return None
        
        file_path = os.path.join(state.download_dir, filename)
        if os.path.exists(file_path):
            return file_path
        return None
    
    async def list_channel_files(
        self,
        client: TelegramClient,
        channel_id: int
    ) -> List[Dict]:
        """List all files from a channel without downloading."""
        files = []
        
        try:
            # Ensure client is connected
            if not client.is_connected():
                await client.connect()
            
            # Get channel entity for name
            try:
                entity = await client.get_entity(channel_id)
                channel_name = getattr(entity, 'title', None) or getattr(entity, 'username', None)
            except:
                channel_name = None
            
            # Collect messages with media
            async for message in client.iter_messages(channel_id, reverse=True):
                if self._has_media(message):
                    file_info = {
                        "message_id": message.id,
                        "filename": "",
                        "size": 0,
                        "mime_type": None,
                        "date": message.date.isoformat() if message.date else None,
                        "is_video": False,
                        "is_photo": False
                    }
                    
                    # Extract file information
                    if isinstance(message.media, MessageMediaDocument):
                        doc = message.media.document
                        if doc:
                            file_info["size"] = doc.size
                            file_info["mime_type"] = doc.mime_type
                            
                            # Check if it's a video
                            for attr in doc.attributes:
                                if hasattr(attr, 'video'):
                                    file_info["is_video"] = True
                                    break
                            
                            # Get filename
                            for attr in doc.attributes:
                                if hasattr(attr, 'file_name'):
                                    file_info["filename"] = attr.file_name
                                    break
                            
                            if not file_info["filename"]:
                                # Generate filename from mime type
                                ext = ""
                                if file_info["mime_type"]:
                                    if "/" in file_info["mime_type"]:
                                        ext = "." + file_info["mime_type"].split("/")[1]
                                file_info["filename"] = f"file_{message.id}{ext}"
                    
                    elif isinstance(message.media, MessageMediaPhoto):
                        file_info["is_photo"] = True
                        file_info["filename"] = f"photo_{message.id}.jpg"
                        file_info["mime_type"] = "image/jpeg"
                    
                    files.append(file_info)
            
            return files
            
        except ChannelInvalidError:
            raise ValueError("Invalid channel")
        except ChannelPrivateError:
            raise ValueError("Channel is private or access denied")
        except Exception as e:
            raise ValueError(f"Failed to list files: {str(e)}")
    
    async def download_single_file(
        self,
        client: TelegramClient,
        channel_id: int,
        message_id: int,
        session_id: str
    ) -> str:
        """Download a single file by message ID."""
        try:
            # Ensure client is connected
            if not client.is_connected():
                await client.connect()
            
            # Get the message
            message = await client.get_messages(channel_id, ids=message_id)
            
            if not message or not self._has_media(message):
                raise ValueError("Message not found or has no media")
            
            # Get download directory
            download_dir = self._get_download_dir(session_id, channel_id)
            
            # Download the file
            filepath = await message.download_media(file=download_dir)
            
            if not filepath:
                raise ValueError("Failed to download file")
            
            return filepath
            
        except Exception as e:
            raise ValueError(f"Failed to download file: {str(e)}")
    
    async def download_multiple_files(
        self,
        client: TelegramClient,
        channel_id: int,
        message_ids: List[int],
        session_id: str
    ) -> List[Dict]:
        """Download multiple files by message IDs. Returns list of downloaded file info."""
        downloaded_files = []
        download_dir = self._get_download_dir(session_id, channel_id)
        
        try:
            # Ensure client is connected
            if not client.is_connected():
                await client.connect()
            
            for message_id in message_ids:
                try:
                    # Get the message
                    message = await client.get_messages(channel_id, ids=message_id)
                    
                    if not message or not self._has_media(message):
                        continue
                    
                    # Download the file
                    filepath = await message.download_media(file=download_dir)
                    
                    if filepath:
                        filename = os.path.basename(filepath)
                        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                        
                        downloaded_files.append({
                            "message_id": message_id,
                            "filename": filename,
                            "size": file_size,
                            "path": filepath,
                            "success": True
                        })
                except Exception as e:
                    downloaded_files.append({
                        "message_id": message_id,
                        "filename": None,
                        "size": 0,
                        "path": None,
                        "success": False,
                        "error": str(e)
                    })
            
            return downloaded_files
            
        except Exception as e:
            raise ValueError(f"Failed to download files: {str(e)}")

