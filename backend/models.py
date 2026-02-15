from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum


class SendCodeRequest(BaseModel):
    phone: str
    api_id: int
    api_hash: str


class SendCodeResponse(BaseModel):
    session_id: str
    status: str
    message: str
    token: Optional[str] = None  # Only present if already authorized


class VerifyCodeRequest(BaseModel):
    session_id: str
    code: str
    password: Optional[str] = None  # For 2FA


class VerifyCodeResponse(BaseModel):
    token: str
    user_info: Dict
    status: str


class DownloadStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StartDownloadRequest(BaseModel):
    channel: str  # Can be channel link, @username, or channel ID


class StartDownloadResponse(BaseModel):
    download_id: str
    status: str
    message: str


class FileInfo(BaseModel):
    filename: str
    size: int
    path: str
    download_url: str


class DownloadStatusResponse(BaseModel):
    download_id: str
    status: DownloadStatus
    progress: float  # 0-100
    total_files: int
    downloaded_files: int
    files: List[FileInfo]
    current_file: Optional[str] = None
    error: Optional[str] = None


class ChannelFileInfo(BaseModel):
    message_id: int
    filename: str
    size: int
    mime_type: Optional[str] = None
    date: Optional[str] = None
    is_video: bool = False
    is_photo: bool = False


class ListChannelFilesRequest(BaseModel):
    channel: str  # Can be channel link, @username, or channel ID


class ListChannelFilesResponse(BaseModel):
    channel_id: int
    channel_name: Optional[str] = None
    files: List[ChannelFileInfo]
    total_count: int


class DownloadAllRequest(BaseModel):
    channel: str
    message_ids: List[int]  # List of message IDs to download

