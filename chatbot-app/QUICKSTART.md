# Quick Setup Guide

## Immediate Testing (Before Installing Dependencies)

### Step 1: Set up your credentials
Edit `backend/.env` and replace the placeholder values:
```
CLIENT_ID=your_actual_client_id_here
CLIENT_SECRET=your_actual_client_secret_here
```

### Step 2: Install Backend Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 4: Start the Application

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
```

### Step 5: Test the Application
- Open http://localhost:3003 in your browser
- Type a message like "Show me all users from the database"
- The AI should respond with a SQL query

## Quick Test Command
After setting up credentials, you can use:
```bash
./start-dev.sh
```

## Troubleshooting
- If you get import errors, make sure you're in the virtual environment
- If CORS errors occur, ensure Flask-CORS is installed
- Check the console logs for authentication issues
