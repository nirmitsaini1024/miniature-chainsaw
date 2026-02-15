# Telegram Channel File Downloader

A modern web application to browse and download files from Telegram channels with a beautiful UI, secure authentication, and batch download support.

![Application Screenshot](Screenshot%20from%202026-02-16%2005-17-17.png)

## 🚀 Features

- **Secure Authentication**: Phone number verification with OTP and 2FA support
- **Channel Browsing**: List and view all files in a Telegram channel
- **Batch Downloads**: Download multiple files at once or individually
- **Modern UI**: Beautiful, responsive interface with dark mode support
- **Real-time Progress**: Track download progress in real-time
- **File Management**: Organize and manage downloaded files

## 📁 Project Structure

```
deploy/
├── backend/          # FastAPI backend server
│   ├── main.py       # FastAPI application entry point
│   ├── models.py     # Pydantic models and schemas
│   ├── telegram_service.py  # Telegram API integration
│   ├── download_service.py  # File download management
│   └── requirements.txt     # Python dependencies
│
└── frontend/         # Next.js frontend application
    ├── app/          # Next.js app router pages
    ├── components/ # React components
    ├── lib/          # API client and types
    └── package.json  # Node.js dependencies
```

## 📋 Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 18+** and **npm** (for frontend)
- **Telegram API Credentials** from [my.telegram.org/apps](https://my.telegram.org/apps)

## 🛠️ Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the setup script (creates venv and installs dependencies):
   ```bash
   chmod +x setup_and_run.sh
   ./setup_and_run.sh
   ```

   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file (if not auto-created):
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   BACKEND_PORT=8000
   ```

4. Run the backend server:
   ```bash
   python main.py
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

   For production, update this to your backend server URL:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-domain.com
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## 🎯 Usage

1. **Start Backend**: Run the backend server first (port 8000)
2. **Start Frontend**: Run the frontend development server (port 3000)
3. **Open Browser**: Navigate to `http://localhost:3000`
4. **Enter API Credentials**: On first visit, enter your Telegram API credentials
5. **Authenticate**: Enter your phone number and verify with OTP
6. **Browse Channels**: Enter a channel name, username, or ID to list files
7. **Download Files**: Download individual files or all files at once

## 🔧 Environment Variables

### Backend (.env)
- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API Hash
- `BACKEND_PORT`: Backend server port (default: 8000)

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## 📦 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Telethon**: Telegram client library
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Frontend
- **Next.js 16**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Phone Number Input**: Phone number input component

## 🚢 Deployment

### Backend Deployment
- Deploy to any Python hosting service (Heroku, Railway, DigitalOcean, etc.)
- Ensure environment variables are set
- The backend runs on the port specified in `BACKEND_PORT` env variable

### Frontend Deployment
- Deploy to Vercel, Netlify, or any static hosting service
- Set `NEXT_PUBLIC_API_URL` to your production backend URL
- Build command: `npm run build`
- Start command: `npm start`

## 📝 API Endpoints

- `POST /api/auth/send-code` - Send OTP to phone number
- `POST /api/auth/verify-code` - Verify OTP code
- `POST /api/channel/list` - List files in a channel
- `POST /api/file/download/{message_id}` - Download a single file
- `POST /api/file/download-all` - Download multiple files

## 🔒 Security Notes

- API credentials are stored in localStorage (consider using secure storage for production)
- Sessions are managed per user
- All API requests require authentication tokens
- CORS is configured for development (update for production)

## 📄 License

This project is open source and available for use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

