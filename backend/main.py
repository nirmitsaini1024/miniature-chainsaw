import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

from models import (
    SendCodeRequest, SendCodeResponse, VerifyCodeRequest, VerifyCodeResponse,
    StartDownloadRequest, StartDownloadResponse, DownloadStatusResponse,
    ListChannelFilesRequest, ListChannelFilesResponse, ChannelFileInfo,
    DownloadAllRequest
)
from telegram_service import TelegramService
from download_service import DownloadService

load_dotenv()

app = FastAPI(title="Telegram Channel Downloader API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (API credentials now come from user input)
telegram_service = TelegramService()
download_service = DownloadService()

# Mount downloads directory for file serving
downloads_path = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(downloads_path, exist_ok=True)


def get_token(authorization: str = Header(None)) -> str:
    """Extract token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization token required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    return authorization.replace("Bearer ", "")


@app.get("/")
async def root():
    return {"message": "Telegram Channel Downloader API"}


@app.post("/api/auth/send-code", response_model=SendCodeResponse)
async def send_code(request: SendCodeRequest):
    """Send OTP code to phone number."""
    try:
        result = await telegram_service.send_code(request.phone, request.api_id, request.api_hash)
        return SendCodeResponse(
            session_id=result["session_id"],
            status=result["status"],
            message=result.get("message", "Code sent"),
            token=result.get("token")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/auth/verify-code", response_model=VerifyCodeResponse)
async def verify_code(request: VerifyCodeRequest):
    """Verify OTP code and complete authentication."""
    try:
        result = await telegram_service.verify_code(
            request.session_id,
            request.code,
            request.password
        )
        return VerifyCodeResponse(
            token=result["token"],
            user_info=result["user_info"],
            status=result["status"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/download/start", response_model=StartDownloadResponse)
async def start_download(request: StartDownloadRequest, token: str = Depends(get_token)):
    """Start downloading files from a channel."""
    try:
        # Get authenticated client
        client = telegram_service.get_client(token)
        if not client:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        await telegram_service.ensure_connected(client)
        
        # Parse channel input
        channel_info = download_service.parse_channel_input(request.channel)
        channel_id = await download_service.resolve_channel_id(client, channel_info)
        
        # Get session ID from token
        session_id = telegram_service.authenticated_sessions.get(token)
        if not session_id:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Start download
        download_id = await download_service.start_download(client, channel_id, session_id)
        
        return StartDownloadResponse(
            download_id=download_id,
            status="started",
            message="Download started successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/download/status/{download_id}", response_model=DownloadStatusResponse)
async def get_download_status(download_id: str, token: str = Depends(get_token)):
    """Get download status and progress."""
    state = download_service.get_download_status(download_id)
    if not state:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Verify token matches session
    session_id = telegram_service.authenticated_sessions.get(token)
    if not session_id or state.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from models import FileInfo, DownloadStatus as DownloadStatusEnum
    
    return DownloadStatusResponse(
        download_id=state.download_id,
        status=DownloadStatusEnum(state.status),
        progress=state.progress,
        total_files=state.total_files,
        downloaded_files=state.downloaded_files,
        files=[FileInfo(**f) for f in state.files],
        current_file=state.current_file,
        error=state.error
    )


@app.post("/api/channel/list", response_model=ListChannelFilesResponse)
async def list_channel_files(request: ListChannelFilesRequest, token: str = Depends(get_token)):
    """List all files from a channel without downloading."""
    try:
        # Get authenticated client
        client = telegram_service.get_client(token)
        if not client:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        await telegram_service.ensure_connected(client)
        
        # Parse channel input
        channel_info = download_service.parse_channel_input(request.channel)
        channel_id = await download_service.resolve_channel_id(client, channel_info)
        
        # Get channel entity for name
        try:
            entity = await client.get_entity(channel_id)
            channel_name = getattr(entity, 'title', None) or getattr(entity, 'username', None)
        except:
            channel_name = None
        
        # List files
        files_data = await download_service.list_channel_files(client, channel_id)
        
        return ListChannelFilesResponse(
            channel_id=channel_id,
            channel_name=channel_name,
            files=[ChannelFileInfo(**f) for f in files_data],
            total_count=len(files_data)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/file/download-all")
async def download_all_files(
    request: DownloadAllRequest,
    token: str = Depends(get_token)
):
    """Download multiple files from a channel."""
    try:
        # Get authenticated client
        client = telegram_service.get_client(token)
        if not client:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        await telegram_service.ensure_connected(client)
        
        # Parse channel input
        channel_info = download_service.parse_channel_input(request.channel)
        channel_id = await download_service.resolve_channel_id(client, channel_info)
        
        # Get session ID from token
        session_id = telegram_service.authenticated_sessions.get(token)
        if not session_id:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Download all files
        downloaded_files = await download_service.download_multiple_files(
            client, channel_id, request.message_ids, session_id
        )
        
        return {
            "success": True,
            "total_requested": len(request.message_ids),
            "total_downloaded": len([f for f in downloaded_files if f.get("success")]),
            "files": downloaded_files
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/file/download/{message_id}")
async def download_single_file(
    message_id: int,
    request: ListChannelFilesRequest,
    token: str = Depends(get_token)
):
    """Download a specific file by message ID from a channel."""
    try:
        # Get authenticated client
        client = telegram_service.get_client(token)
        if not client:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        await telegram_service.ensure_connected(client)
        
        # Parse channel input
        channel_info = download_service.parse_channel_input(request.channel)
        channel_id = await download_service.resolve_channel_id(client, channel_info)
        
        # Get session ID from token
        session_id = telegram_service.authenticated_sessions.get(token)
        if not session_id:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Download the file
        file_path = await download_service.download_single_file(
            client, channel_id, message_id, session_id
        )
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        filename = os.path.basename(file_path)
        
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/download/files/{download_id}/{filename}")
async def download_file(download_id: str, filename: str, token: str = Depends(get_token)):
    """Download a specific file."""
    state = download_service.get_download_status(download_id)
    if not state:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Verify token matches session
    session_id = telegram_service.authenticated_sessions.get(token)
    if not session_id or state.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = download_service.get_download_file_path(download_id, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

