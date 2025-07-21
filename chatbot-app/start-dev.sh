#!/bin/bash

# Development startup script for the chatbot application

echo "🚀 Starting Chatbot Application Development Environment"
echo "======================================================"

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the chatbot-app root directory"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ All prerequisites found"

# Setup backend
echo ""
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start backend in background
echo "Starting Flask backend server..."
python run.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

cd ..

# Setup frontend
echo ""
echo "⚛️  Setting up React frontend..."
cd frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

# Start frontend
echo "Starting React development server..."
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

cd ..

echo ""
echo "🎉 Application started successfully!"
echo "======================================"
echo "Frontend: http://localhost:3003"
echo "Backend:  http://localhost:5001"
echo ""
echo "To stop the application:"
echo "kill $FRONTEND_PID $BACKEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $FRONTEND_PID $BACKEND_PID; exit 0" INT
wait
