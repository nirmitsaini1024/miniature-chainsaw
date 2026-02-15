#!/bin/bash

# Script to set up virtual environment and run the backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env file and add your TELEGRAM_API_ID and TELEGRAM_API_HASH"
    else
        echo "WARNING: .env.example not found. Creating basic .env file..."
        cat > .env << EOF
TELEGRAM_API_ID=37388544
TELEGRAM_API_HASH=a9cb57fe3e8887e67f9b7c4f51edeb5e
BACKEND_PORT=8000
EOF
        echo "Using default API credentials. Please update .env with your own credentials."
    fi
fi

# Run the server
echo "Starting FastAPI server..."
python main.py

