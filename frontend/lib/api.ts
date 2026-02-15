import {
  SendCodeRequest,
  SendCodeResponse,
  VerifyCodeRequest,
  VerifyCodeResponse,
  StartDownloadRequest,
  StartDownloadResponse,
  DownloadStatusResponse,
  ListChannelFilesRequest,
  ListChannelFilesResponse,
  DownloadAllRequest,
  DownloadAllResponse,
} from "./types";

// Get API URL from environment variable, fallback to localhost for development
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function sendCode(data: SendCodeRequest): Promise<SendCodeResponse> {
  return fetchAPI<SendCodeResponse>("/api/auth/send-code", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function verifyCode(data: VerifyCodeRequest): Promise<VerifyCodeResponse> {
  return fetchAPI<VerifyCodeResponse>("/api/auth/verify-code", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function startDownload(
  data: StartDownloadRequest,
  token: string
): Promise<StartDownloadResponse> {
  return fetchAPI<StartDownloadResponse>("/api/download/start", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

export async function getDownloadStatus(
  downloadId: string,
  token: string
): Promise<DownloadStatusResponse> {
  return fetchAPI<DownloadStatusResponse>(`/api/download/status/${downloadId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function getFileDownloadUrl(downloadId: string, filename: string, token: string): string {
  return `${API_URL}/api/download/files/${downloadId}/${encodeURIComponent(filename)}`;
}

export async function downloadFile(downloadId: string, filename: string, token: string): Promise<void> {
  const url = getFileDownloadUrl(downloadId, filename, token);
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to download file");
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

export async function listChannelFiles(
  data: ListChannelFilesRequest,
  token: string
): Promise<ListChannelFilesResponse> {
  return fetchAPI<ListChannelFilesResponse>("/api/channel/list", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

export async function downloadSingleFile(
  channel: string,
  messageId: number,
  token: string
): Promise<void> {
  const url = `${API_URL}/api/file/download/${messageId}`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ channel }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "Failed to download file");
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("content-disposition");
  let filename = `file_${messageId}`;
  
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }

  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

export async function downloadAllFiles(
  data: DownloadAllRequest,
  token: string
): Promise<DownloadAllResponse> {
  return fetchAPI<DownloadAllResponse>("/api/file/download-all", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

