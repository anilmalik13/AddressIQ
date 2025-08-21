# AddressIQ

A comprehensive address intelligence platform with AI-powered address standardization, file processing, and geographic visualization capabilities, powered by Azure OpenAI services.

## Overview

AddressIQ is a full-stack web application that combines a React TypeScript frontend with a Python Flask backend to deliver intelligent address processing, standardization, and visualization. The application features file upload capabilities, real-time address processing, and interactive geographic mapping.

## Features

- **Excel File Upload & Processing**: Upload Excel files containing address data for batch processing
- **AI-Powered Address Standardization**: Advanced address parsing and standardization using Azure OpenAI
- **Interactive Geographic Mapping**: Visual representation of addresses using Leaflet maps with regional filtering
- **Real-time Address Processing**: Individual address standardization with confidence scoring
- **Batch Processing**: Process multiple addresses from uploaded Excel files
- **Backend CLI Tools**: Powerful CSV processor with batch modes, address comparison, and directory management
- **Regional Analysis**: Filter and visualize addresses by region and country
- **Modern React UI**: Responsive interface with tabbed navigation and real-time updates
- **RESTful API**: Clean backend API for frontend-backend communication
- **WSO2 Integration**: Secure authentication through WSO2 gateway for Azure OpenAI services

## Architecture

### Frontend (`/chatbot-app/frontend`)
- **React 18** with TypeScript and modern hooks
- **Redux Toolkit** with Redux Observable for state management
- **Three Main Components**:
  - **File Upload**: Excel file processing with drag-and-drop functionality
  - **Address Processing**: Real-time individual address standardization
  - **Region City Map**: Interactive geographic visualization with Leaflet
- **Responsive Design**: Cross-platform compatibility with tabbed navigation
- **API Integration**: Axios-based service layer with proxy configuration

### Backend (`/chatbot-app/backend`)
- **Python Flask** application with modular architecture
- **Azure OpenAI Integration** through WSO2 gateway with OAuth2 authentication
- **Address Processing Engine**: AI-powered standardization with confidence scoring
- **RESTful API**: Clean endpoints for chat and address processing
- **Configuration Management**: Flexible prompt and system configuration
- **Data Processing**: CSV handling and batch address processing capabilities

## Project Structure

```
AddressIQ/
├── README.md
├── chatbot-app/                 # Main application directory
│   ├── QUICKSTART.md           # Quick setup guide
│   ├── README.md               # Application-specific documentation
│   ├── start-dev.sh            # Development startup script
│   ├── frontend/               # React TypeScript frontend
│   │   ├── package.json        # Frontend dependencies and scripts
│   │   ├── tsconfig.json       # TypeScript configuration
│   │   ├── README.md           # Frontend documentation
│   │   ├── public/
│   │   │   └── index.html      # Main HTML template
│   │   └── src/
│   │       ├── App.tsx         # Main app component with tabbed navigation
│   │       ├── App.css         # Global application styles
│   │       ├── index.tsx       # Application entry point
│   │       ├── index.css       # Global CSS styles
│   │       ├── setupProxy.js   # Development proxy configuration
│   │       ├── components/     # React components
│   │       │   ├── FileUpload/ # Excel file upload component
│   │       │   │   ├── FileUpload.tsx
│   │       │   │   ├── FileUpload.css
│   │       │   │   └── index.ts
│   │       │   ├── AddressProcessing/ # Address standardization component
│   │       │   │   ├── AddressProcessing.tsx
│   │       │   │   ├── AddressProcessing.css
│   │       │   │   └── index.ts
│   │       │   ├── RegionCityMap/ # Interactive map component
│   │       │   │   ├── RegionCityMap.tsx
│   │       │   │   ├── RegionCityMap.css
│   │       │   │   └── index.ts
│   │       ├── store/              # Redux store setup
│   │       │   ├── index.ts        # Store configuration
│   │       │   ├── slices/         # Redux slices
│   │       │   │   ├── fileUploadSlice.ts      # File upload state management
│   │       │   │   └── addressProcessingSlice.ts # Address processing state
│   │       │   └── epics/          # Redux Observable epics
│   │       │       ├── index.ts
│   │       │       ├── fileUploadEpic.ts       # File upload side effects
│   │       │       └── addressProcessingEpic.ts # Address processing side effects
│   │       ├── services/           # API services
│   │       │   └── api.ts          # Axios configuration and API calls
│   │       ├── hooks/              # Custom React hooks
│   │       │   └── redux.ts        # Typed Redux hooks
│   │       └── types/              # TypeScript type definitions
│   │           └── index.ts        # Application type definitions
│   └── backend/                    # Python Flask backend
│       ├── requirements.txt        # Python dependencies
│       ├── run.py                 # Application entry point
│       ├── ADDRESS_STANDARDIZATION_README.md # Address processing documentation
│       ├── csv_address_processor.py # CSV processing utilities
│       ├── debug_geocoding.py     # Geocoding debugging tools
│       ├── example_address_standardization.py # Usage examples
│       ├── site_addresses_sample.csv # Sample data files
│       ├── test_global_addresses.csv
│       └── app/                   # Main application package
│           ├── __init__.py        # Package initialization
│           ├── main.py            # Flask application and routes
│           ├── config/            # Configuration management
│           │   ├── address_config.py # Address processing configuration
│           │   └── address_config_backup.py # Backup configuration
│           ├── models/            # Data models
│           │   ├── __init__.py
│           │   └── chat.py        # Chat-related models
│           └── services/          # Business logic services
│               ├── __init__.py
│               └── azure_openai.py # Azure OpenAI integration service
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AddressIQ/chatbot-app
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file in backend directory
   cd backend
   cp .env.example .env  # If example exists, or create new .env
   # Edit .env with your credentials:
   # CLIENT_ID=your_actual_client_id_here
   # CLIENT_SECRET=your_actual_client_secret_here
   # WSO2_AUTH_URL=https://api-test.cbre.com:443/token
   # AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
   ```

3. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Start the application**
   ```bash
   # Use the provided script for easy development
   ./start-dev.sh
   
   # Or start services individually:
   # Terminal 1 - Backend: 
   cd backend && python run.py
   
   # Terminal 2 - Frontend: 
   cd frontend && npm start
   ```

6. **Access the application**
   - Frontend: http://localhost:3003
   - Backend API: http://localhost:5001

## Backend CLI (CSV processor) – current capabilities

In addition to the web app, the backend includes a CLI for addressing CSVs and free-text addresses:

- CSV file: `python csv_address_processor.py input.csv`
- Batch modes (use `inbound/`, `outbound/`, `archive/` under the base dir):
   - Process all files: `python csv_address_processor.py --batch-process`
   - Process all comparison files: `python csv_address_processor.py --batch-compare`
   - Set base directory: `python csv_address_processor.py --batch-process --base-dir "C:\\AddressIQ\\chatbot-app\\backend"`
- Direct address processing:
   - Single or multiple: `python csv_address_processor.py --address "123 Main St" "456 Oak Ave"`
   - Force country: `--country UK`; output formats: `--format json|formatted|detailed`
   - Save output: `--output results.json`
- Address comparison:
   - Two addresses: `python csv_address_processor.py --compare "A1" "A2"`
   - CSV pairs: `python csv_address_processor.py comparison.csv --compare-csv`
- CSV options: `-c/--column`, `-b/--batch-size 5` (default 5), `-o/--output`, `--no-free-apis`
- Utilities: `--db-stats`, `--test-apis`

## Technologies Used

### Frontend
- **React 18** with TypeScript
- **Redux Toolkit** with Redux Observable for state management
- **React Leaflet** for interactive mapping
- **Axios** for HTTP client communication
- **Country-State-City** for geographic data
- **CSS3** with component-specific styling

### Backend
- **Python 3.11+** with Flask web framework
- **Azure OpenAI SDK** for AI-powered address processing
- **WSO2 Gateway** for secure API access
- **Pandas** for data manipulation and CSV processing
- **Python-dotenv** for environment configuration
- **Flask-CORS** for cross-origin resource sharing

### Development & Infrastructure
- **TypeScript** for type safety
- **npm/Node.js** for frontend package management
- **pip/virtualenv** for Python dependency management
- **Git** for version control

## Key Features Breakdown

### 📁 File Upload Component
- **Excel File Processing**: Support for .xls and .xlsx files
- **Drag & Drop Interface**: Intuitive file selection
- **Progress Tracking**: Real-time upload progress indicators
- **File Validation**: Automatic file type and size validation

### 🏠 Address Processing Component
- **AI-Powered Standardization**: Uses Azure OpenAI for intelligent address parsing
- **Real-time Processing**: Individual address standardization with instant results
- **Confidence Scoring**: Quality assessment for processed addresses
- **Copy Functionality**: Easy result copying for further use

### 🗺️ Regional Map Component
- **Interactive Mapping**: Leaflet-based geographic visualization
- **Regional Filtering**: Filter addresses by region and country
- **Geocoding Integration**: Automatic coordinate generation for addresses
- **Marker Clustering**: Efficient display of multiple address points

### 🔧 Backend Services
- **WSO2 Authentication**: Secure token-based authentication
- **Azure OpenAI Integration**: Advanced language model processing
- **Configurable Prompts**: Customizable system prompts for different use cases
- **Batch Processing**: Handle multiple addresses efficiently

## Development

### Backend Development
The backend is built with Flask and follows a modular architecture:

- **Main Application** (`app/main.py`): Flask app with CORS enabled and API routes
- **Azure OpenAI Service** (`app/services/azure_openai.py`): Handles authentication and AI requests
- **Configuration** (`app/config/address_config.py`): Customizable prompts and settings
- **Models** (`app/models/`): Data structures for chat and address processing

### Frontend Development
The frontend uses modern React patterns with Redux for state management:

- **Component Architecture**: Modular components with CSS modules
- **State Management**: Redux Toolkit with Redux Observable for async operations
- **Type Safety**: Full TypeScript implementation with strict type checking
- **API Layer**: Centralized Axios configuration with proxy setup

### Configuration Management
- **Environment Variables**: Secure credential management via .env files
- **Prompt Configuration**: Customizable AI prompts for different address processing needs
- **API Settings**: Configurable endpoints and authentication parameters

## Contributing

This project follows modern development practices:

- **Version Control**: Git with descriptive commit messages
- **Code Organization**: Modular, maintainable structure with clear separation of concerns
- **Type Safety**: TypeScript for frontend, Python type hints for backend
- **Documentation**: Comprehensive README files and inline code documentation
- **Testing**: Component and service-level testing capabilities

## API Endpoints

### Backend API Routes
- **POST `/api/chat`**: Process address standardization requests through AI
  - Body: `{ "message": "address_text", "system_prompt": "optional_prompt", "prompt_type": "general|address" }`
  - Response: Standardized address data with confidence scores

### Frontend Routes
- **File Upload Tab**: Excel file processing interface
- **Address Processing Tab**: Individual address standardization
- **Region Map Tab**: Geographic visualization and filtering

## License

[Add your license information here]

## Support

For questions, issues, or contributions, please refer to the project documentation:
- **Backend Documentation**: `chatbot-app/backend/ADDRESS_STANDARDIZATION_README.md`
- **Frontend Documentation**: `chatbot-app/frontend/README.md`
- **Quick Setup**: `chatbot-app/QUICKSTART.md`

---

**AddressIQ** - Comprehensive address intelligence platform with AI-powered standardization, file processing, and geographic visualization capabilities.
