export interface SendCodeRequest {
  phone: string;
  api_id: number;
  api_hash: string;
}

export interface SendCodeResponse {
  session_id: string;
  status: string;
  message: string;
  token?: string; // Only present if already authorized
}

export interface VerifyCodeRequest {
  session_id: string;
  code: string;
  password?: string;
}

export interface VerifyCodeResponse {
  token: string;
  user_info: {
    id: number;
    first_name?: string;
    last_name?: string;
    username?: string;
    phone?: string;
  };
  status: string;
}

export interface StartDownloadRequest {
  channel: string;
}

export interface StartDownloadResponse {
  download_id: string;
  status: string;
  message: string;
}

export type DownloadStatus = "pending" | "in_progress" | "completed" | "failed";

export interface FileInfo {
  filename: string;
  size: number;
  path: string;
  download_url: string;
}

export interface DownloadStatusResponse {
  download_id: string;
  status: DownloadStatus;
  progress: number;
  total_files: number;
  downloaded_files: number;
  files: FileInfo[];
  current_file?: string;
  error?: string;
}

export interface ChannelFileInfo {
  message_id: number;
  filename: string;
  size: number;
  mime_type?: string;
  date?: string;
  is_video: boolean;
  is_photo: boolean;
}

export interface ListChannelFilesRequest {
  channel: string;
}

export interface ListChannelFilesResponse {
  channel_id: number;
  channel_name?: string;
  files: ChannelFileInfo[];
  total_count: number;
}

export interface DownloadAllRequest {
  channel: string;
  message_ids: number[];
}

export interface DownloadAllResponse {
  success: boolean;
  total_requested: number;
  total_downloaded: number;
  files: Array<{
    message_id: number;
    filename: string | null;
    size: number;
    path: string | null;
    success: boolean;
    error?: string;
  }>;
}

