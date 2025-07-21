# Chatbot Application

This project is a chatbot application built with a React frontend and a Python Flask backend. The application connects to Azure OpenAI through WSO2 to provide intelligent responses to user queries, specifically designed for generating SQL queries.

## 🚀 Quick Start

**Option 1: Use the automated setup script**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

**Option 2: Manual setup (see detailed instructions below)**

## Project Structure

```
chatbot-app/
├── frontend/             # Frontend React application
│   ├── src/
│   │   ├── components/   # React components for chat interface
│   │   │   ├── Chat.tsx          # Main chat container
│   │   │   ├── ChatInput.tsx     # User input component
│   │   │   └── ChatMessage.tsx   # Message display component
│   │   ├── services/     # API service for backend communication
│   │   │   └── api.ts            # Backend API integration
│   │   ├── types/        # TypeScript types and interfaces
│   │   │   └── index.ts          # Type definitions
│   │   ├── App.tsx       # Main application component
│   │   ├── index.tsx     # Entry point of the React application
│   │   └── index.css     # Application styling
│   ├── public/           # Public assets
│   ├── package.json      # NPM configuration with dependencies
│   └── tsconfig.json     # TypeScript configuration
├── backend/              # Backend Python Flask application
│   ├── app/
│   │   ├── __init__.py   # Flask app initialization
│   │   ├── main.py       # Main Flask application with CORS
│   │   ├── services/     # Backend services
│   │   │   └── azure_openai.py   # Azure OpenAI integration
│   │   └── models/       # Data models for chat interactions
│   │       └── chat.py           # Chat message models
│   ├── requirements.txt  # Python dependencies (includes Flask-CORS)
│   └── .env             # Environment variables (secure)
├── start-dev.sh         # Development startup script
└── README.md            # Project documentation
```

## 🔧 Prerequisites

- **Node.js** (v14 or higher) and npm
- **Python 3.7+**
- **Azure OpenAI** account with access through WSO2
- **Valid WSO2 credentials**

## 📋 Environment Setup

### 1. Backend Configuration

Navigate to the backend directory and update the `.env` file:

```bash
cd backend
```

Edit `.env` with your actual credentials:
```env
# WSO2 Configuration
WSO2_AUTH_URL=https://api-test.cbre.com:443/token

# Azure OpenAI Configuration  
AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id

# Client Credentials (Replace with actual values)
CLIENT_ID=your_actual_client_id
CLIENT_SECRET=your_actual_client_secret

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 2. Backend Setup (Manual)

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python app/main.py
```

The backend will run on `http://localhost:5001`

### 3. Frontend Setup (Manual)

```bash
cd frontend

# Install dependencies
npm install

# Start the development server (runs on port 3003)
npm start
```

The frontend will run on `http://localhost:3003`

## 🌟 Features

- **Real-time Chat Interface**: Modern React-based chat UI with message history
- **Azure OpenAI Integration**: Connects to Azure OpenAI through WSO2 proxy
- **SQL Query Generation**: Specialized for creating safe SQL SELECT statements
- **OAuth2 Authentication**: Secure client credentials flow with WSO2
- **CORS Support**: Proper frontend-backend communication
- **Error Handling**: Comprehensive error management and user feedback
- **TypeScript Support**: Full type safety in frontend components
- **Responsive Design**: Mobile-friendly chat interface
- **Environment Security**: All credentials stored in environment variables

## 🔒 Security Features

- Client credentials stored in environment variables
- No hardcoded API keys in source code
- CORS protection configured
- Bearer token authentication
- Request/response logging for debugging

## 🛠 API Endpoints

### Backend API

- **POST** `/api/chat`
  - **Body**: `{ "message": "user query", "system_prompt": "optional custom prompt" }`
  - **Response**: Azure OpenAI completion response
  - **Headers**: `Content-Type: application/json`

## 🎯 Usage

1. Start both frontend and backend servers
2. Navigate to `http://localhost:3003`
3. Type your SQL query request in the chat interface
4. The AI will respond with a SQL SELECT statement
5. Chat history is maintained during the session

### Example Queries

- "Show me all customers from New York"
- "Get the top 10 products by sales"
- "Find employees hired in the last 6 months"

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure Flask-CORS is installed and configured
2. **Authentication Failures**: Verify CLIENT_ID and CLIENT_SECRET in .env
3. **Module Not Found**: Run `npm install` in frontend and `pip install -r requirements.txt` in backend
4. **Port Conflicts**: Ensure ports 3000 and 5000 are available

### Debug Mode

The application includes extensive logging. Check the console output for:
- Token acquisition status
- API request/response details
- Error messages with stack traces

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.

## 🔄 Recent Updates

- ✅ Fixed frontend-backend communication
- ✅ Added proper TypeScript interfaces
- ✅ Implemented secure environment variable usage
- ✅ Added comprehensive styling
- ✅ Created automated development setup
- ✅ Added CORS support for cross-origin requests
- ✅ Enhanced error handling and user feedback