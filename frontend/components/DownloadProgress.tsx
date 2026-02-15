"use client";

import { DownloadStatusResponse, FileInfo } from "@/lib/types";
import { API_URL } from "@/lib/api";

interface DownloadProgressProps {
  status: DownloadStatusResponse;
  token: string;
}

export default function DownloadProgress({ status, token }: DownloadProgressProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "in_progress":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      case "in_progress":
        return "In Progress";
      default:
        return "Pending";
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const handleDownload = async (downloadId: string, filename: string) => {
    try {
      const url = `${API_URL}/api/download/files/${downloadId}/${encodeURIComponent(filename)}`;
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
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download file. Please try again.");
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-white text-sm font-medium ${getStatusColor(status.status)}`}>
            {getStatusText(status.status)}
          </span>
          {status.current_file && (
            <span className="text-sm text-gray-600">Downloading: {status.current_file}</span>
          )}
        </div>
        {status.error && (
          <span className="text-sm text-red-600">Error: {status.error}</span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{Math.round(status.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${getStatusColor(status.status)}`}
            style={{ width: `${status.progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{status.downloaded_files} / {status.total_files} files</span>
        </div>
      </div>

      {/* Files List */}
      {status.files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">Downloaded Files ({status.files.length})</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {status.files.map((file: FileInfo, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.filename}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  onClick={() => handleDownload(status.download_id, file.filename)}
                  className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

