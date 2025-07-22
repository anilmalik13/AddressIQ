# AddressIQ

A modern chatbot application with advanced address intelligence capabilities, powered by Azure OpenAI services.

## Overview

AddressIQ is a full-stack web application that combines a React TypeScript frontend with a Python Flask backend to deliver intelligent chat interactions with specialized address processing and standardization features.

## Features

- **Interactive Chat Interface**: Modern, responsive chat UI built with React and TypeScript
- **Azure OpenAI Integration**: Powered by Azure's GPT models for intelligent conversations
- **Address Standardization**: Advanced address processing and validation capabilities
- **Real-time Communication**: Seamless frontend-backend integration
- **Modern Tech Stack**: Built with the latest web technologies

## Architecture

### Frontend (`/frontend`)
- **React 18** with TypeScript
- **Modern UI Components**: Chat interface, message handling, and input controls
- **Responsive Design**: Works across desktop and mobile devices
- **API Integration**: Clean service layer for backend communication

### Backend (`/backend`)
- **Python Flask** application
- **Azure OpenAI Services** integration
- **Address Processing Engine**: Standardization and validation
- **RESTful API**: Clean endpoints for frontend communication
- **Modular Architecture**: Organized services and models

## Project Structure

```
AddressIQ/
├── README.md
├── QUICKSTART.md
├── start-dev.sh
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.tsx                # Main app component with routing
│       ├── App.css                # Global styles
│       ├── index.tsx              # Application entry point
│       ├── components/            # React components
│       │   ├── FileUpload/        # File upload feature
│       │   ├── AddressProcessing/ # Address processing feature
│       │   ├── Chat.tsx           # Legacy chat component
│       │   ├── ChatInput.tsx
│       │   └── ChatMessage.tsx
│       ├── store/                 # Redux store setup
│       │   ├── index.ts
│       │   ├── slices/
│       │   └── epics/
│       ├── services/              # Axios API configuration
│       ├── hooks/                 # Typed Redux hooks
│       └── types/                 # TypeScript type definitions
└── backend/
    ├── requirements.txt
    ├── run.py
    ├── example_address_standardization.py
    ├── ADDRESS_STANDARDIZATION_README.md
    └── app/
        ├── main.py
        ├── config/
        ├── models/
        └── services/
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AddressIQ
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   - Set up your Azure OpenAI credentials
   - Configure any required API keys

5. **Start the application**
   ```bash
   # Use the provided script for easy development
   ./start-dev.sh
   
   # Or start services individually:
   # Backend: python backend/run.py
   # Frontend: cd frontend && npm start
   ```

## Technologies Used

### Frontend
- React 18
- TypeScript
- Modern CSS/Styling
- HTTP Client for API communication

### Backend
- Python 3.11+
- Flask web framework
- Azure OpenAI SDK
- Address processing libraries

## Contributing

This project follows modern development practices:

- **Version Control**: Git with descriptive commit messages
- **Code Organization**: Modular, maintainable structure
- **Type Safety**: TypeScript for frontend, Python type hints
- **Documentation**: Comprehensive README and inline documentation

## License

[Add your license information here]

## Support

For questions, issues, or contributions, please [add contact information or issue tracker link].

---

**AddressIQ** - Intelligent chat with smart address processing capabilities.
