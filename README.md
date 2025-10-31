# AddressIQ

A comprehensive address intelligence platform with AI-powered address standardization, file processing, and geographic visualization capabilities, powered by Azure OpenAI services.

## Overview

AddressIQ is a full-stack web application that combines a React TypeScript frontend with a Python Flask backend to deliver intelligent address processing, standardization, and visualization. The application features multiple processing modes, public API endpoints, real-time address processing, and interactive geographic mapping.

## Features

### Core Functionality
- **Async File Upload & Processing**: Upload Excel/CSV files with asynchronous background processing - continue working while files process
- **Processing History**: Track and manage all file processing jobs with status monitoring, automatic cleanup, and 7-day retention
- **Database Connect (Table/Query)**: Fetch rows directly from SQL Server/Azure SQL using connection strings, then standardize and preview results with pagination
- **Compare Upload Processing**: Upload files for address comparison and analysis between datasets with async processing
- **AI-Powered Address Standardization**: Advanced address parsing and standardization using Azure OpenAI with confidence scoring
- **Single & Batch Address Processing**: Process individual addresses or multiple addresses in real-time
- **Interactive Geographic Mapping**: Visual representation of addresses using Leaflet maps with regional filtering
- **Job Management**: View job history, filter by status, download completed files, and monitor expiration times

### Public API
- **RESTful API v1**: Comprehensive API endpoints for programmatic access to all features
- **API Documentation Interface**: Interactive accordion-based UI for testing and exploring API endpoints
- **Sample File Downloads**: Downloadable sample files for testing file upload and compare functionality
- **No Authentication Required**: Simplified access for public API endpoints

### Technical Features
- **Asynchronous Processing**: Non-blocking file uploads with background processing using Python threading
- **SQLite Job Database**: Persistent job tracking with automatic cleanup and database migration support
- **Webhook Notifications**: Optional webhook callbacks for job completion events
- **Backend CLI Tools**: Powerful CSV processor with batch modes, address comparison, and directory management
- **Regional Analysis**: Filter and visualize addresses by region and country
- **Modern React UI**: Responsive interface with tabbed navigation and real-time updates
- **Redux State Management**: Comprehensive state management with Redux Toolkit and RxJS epics
- **WSO2 Integration**: Secure authentication through WSO2 gateway for Azure OpenAI services
- **CBRE Branding**: Modern green theme (#003f2d) with professional styling

## Architecture

### Frontend (`/chatbot-app/frontend`)
- **React 18** with TypeScript and modern hooks
- **Redux Toolkit** with Redux Observable for state management
- **Main Components**:
  - **File Upload**: Excel/CSV file processing with drag-and-drop functionality and async processing
  - **Address Processing**: Real-time individual address standardization
  - **Compare Upload**: File comparison and analysis functionality with async processing
  - **Database Connect**: Table/Query mode to pull data from databases and run standardization pipeline with preview/download
  - **Public API**: Interactive API documentation and testing interface with accordion UI
  - **Region City Map**: Interactive geographic visualization with Leaflet
  - **Processing History**: Full job tracking with filtering, status monitoring, and file downloads
- **Responsive Design**: Cross-platform compatibility with tabbed navigation
- **API Integration**: Axios-based service layer with proxy configuration
- **CBRE Theme**: Modern green styling (#003f2d) with professional design

### Backend (`/chatbot-app/backend`)
- **Python Flask** application with modular architecture
- **Azure OpenAI Integration** through WSO2 gateway with OAuth2 authentication
- **Address Processing Engine**: AI-powered standardization with confidence scoring
- **RESTful API v1**: Comprehensive endpoints for all features including:
  - `/api/v1/files/upload` - Synchronous file upload and processing
  - `/api/v1/files/upload-async` - Asynchronous file upload with background processing
  - `/api/v1/files/status/<processing_id>` - Check async job status
  - `/api/v1/files/jobs` - Retrieve job history and management
  - `/api/v1/addresses/standardize` - Single address standardization
  - `/api/v1/addresses/batch-standardize` - Batch address processing
  - `/api/v1/compare/upload` - File comparison processing
  - `/api/v1/database/connect` - Database connection and processing
  - `/api/v1/samples/*` - Sample file downloads
  - `/api/v1/admin/stats` - Job statistics and metrics
  - `/api/v1/admin/cleanup` - Manual cleanup of expired jobs
- **SQLite Job Persistence**: Automatic job tracking with database migration support
- **Configuration Management**: Flexible prompt and system configuration
- **Data Processing**: CSV handling and batch address processing capabilities
- **Database Integration**: Support for SQL Server/Azure SQL connections

## Project Structure

```
AddressIQ/
├── README.md                    # This file - project overview and setup
├── chatbot-app/                 # Main application directory
│   ├── README.md               # Application-specific documentation
│   ├── QUICKSTART.md           # Quick setup guide
│   ├── start-dev.sh            # Development startup script
│   ├── frontend/               # React TypeScript frontend
│   │   ├── package.json        # Frontend dependencies
│   │   ├── tsconfig.json       # TypeScript configuration
│   │   ├── build/              # Production build output
│   │   ├── public/             # Static files
│   │   └── src/                # Source code
│   │       ├── App.tsx         # Main application component with routing
│   │       ├── components/     # React components
│   │       │   ├── FileUpload/ # File upload functionality
│   │       │   ├── AddressProcessing/ # Address standardization
│   │       │   ├── CompareUpload/ # File comparison features
│   │       │   ├── DatabaseConnect/ # Database integration
│   │       │   ├── PublicAPI/  # API documentation and testing interface
│   │       │   └── RegionCityMap/ # Geographic visualization
│   │       ├── store/          # Redux store configuration
│   │       ├── services/       # API service layer
│   │       └── types/          # TypeScript type definitions
│   └── backend/                # Python Flask backend
│       ├── README.md           # Backend-specific documentation
│       ├── requirements.txt    # Python dependencies
│       ├── run.py              # Application entry point
│       ├── app/                # Flask application
│       │   ├── main.py         # Main Flask app with API routes
│       │   ├── config/         # Configuration files
│       │   ├── models/         # Data models
│       │   └── services/       # Business logic services
│       ├── database/           # SQLite job database
│       │   ├── job_manager.py  # Job persistence and management
│       │   └── jobs.db         # SQLite database (auto-created)
│       ├── inbound/            # File upload directory
│       ├── outbound/           # Processed file output
│       ├── archive/            # Archived files
│       └── samples/            # Sample files for API testing
└── .venv/                      # Python virtual environment
```

## Quick Start

### Prerequisites
- **Node.js** 16+ and npm (for frontend)
- **Python** 3.8+ and pip (for backend)
- **SQL Server** or **Azure SQL Database** (optional, for database features)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/anilmalik13/AddressIQ.git
   cd AddressIQ
   ```

2. **Backend Setup**
   ```bash
   cd chatbot-app/backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   python run.py
   ```

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd chatbot-app/frontend
   npm install
   npm start
   ```

4. **Access the Application**
   - Frontend: http://localhost:3003
   - Backend API: http://localhost:5001
   - API Documentation: http://localhost:3003 (Public API tab)
   - Processing History: http://localhost:3003 (Processing History tab)

### Using the Public API

AddressIQ provides a comprehensive RESTful API for programmatic access to all features:

#### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/files/upload` | POST | Upload Excel/CSV files for synchronous processing |
| `/api/v1/files/upload-async` | POST | Upload files for async background processing |
| `/api/v1/files/status/<processing_id>` | GET | Check status of async job |
| `/api/v1/files/jobs` | GET | Retrieve job history (supports filtering by status/component) |
| `/api/v1/addresses/standardize` | POST | Standardize a single address |
| `/api/v1/addresses/batch-standardize` | POST | Standardize multiple addresses |
| `/api/v1/compare/upload` | POST | Upload files for comparison analysis |
| `/api/v1/database/connect` | POST | Connect to database and process addresses |
| `/api/v1/samples/file-upload` | GET | Download sample upload file |
| `/api/v1/samples/compare-upload` | GET | Download sample compare file |
| `/api/v1/admin/stats` | GET | View job statistics and metrics |
| `/api/v1/admin/cleanup` | POST | Manually trigger cleanup of expired jobs |

#### Example API Usage

**Single Address Standardization:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"address": "123 Main St, New York, NY 10001"}' \
  http://localhost:5001/api/v1/addresses/standardize
```

**Synchronous File Upload:**
```bash
curl -X POST -F "file=@addresses.xlsx" \
  http://localhost:5001/api/v1/files/upload
```

**Asynchronous File Upload:**
```bash
curl -X POST -F "file=@addresses.xlsx" -F "webhook_url=https://your-webhook.com/callback" \
  http://localhost:5001/api/v1/files/upload-async
# Returns: {"processing_id": "abc123", "status": "processing"}
```

**Check Job Status:**
```bash
curl http://localhost:5001/api/v1/files/status/abc123
```

**Get Job History:**
```bash
curl http://localhost:5001/api/v1/files/jobs?status=completed&component=upload
```

For complete API documentation and interactive testing, visit the **Public API** tab in the web interface.

## Technologies Used

### Frontend
- **React 18** with TypeScript for modern component-based architecture
- **Redux Toolkit** with Redux Observable for comprehensive state management
- **React Leaflet** for interactive mapping and geographic visualization
- **Axios** for HTTP client communication with the backend API
- **CSS3** with custom styling and CBRE green theme (#003f2d)

### Backend
- **Python 3.11+** with Flask web framework for RESTful API development
- **Azure OpenAI SDK** for AI-powered address processing and standardization
- **WSO2 Gateway** for secure API access and authentication
- **Pandas** for data manipulation and CSV/Excel processing
- **pyodbc** for SQL Server/Azure SQL database connectivity
- **Flask-CORS** for cross-origin resource sharing

### Development & Infrastructure
- **TypeScript** for type safety across the frontend application
- **Python Virtual Environment** for isolated dependency management
- **npm/Node.js** ecosystem for frontend package management
- **Git** for version control and collaboration

## Key Components

### 📁 File Upload & Processing
- **Multi-format Support**: Excel (.xlsx, .xls) and CSV file processing
- **Batch Processing**: Handle large datasets efficiently
- **Progress Tracking**: Real-time upload and processing status
- **Sample Downloads**: Downloadable template files for testing

### 🏠 Address Standardization
- **AI-Powered Processing**: Azure OpenAI for intelligent address parsing
- **Single & Batch Modes**: Process individual addresses or multiple addresses
- **Confidence Scoring**: Quality assessment for processed addresses
- **Global Support**: Multi-country address standardization

### 📊 Compare & Analysis
- **File Comparison**: Upload and compare address datasets
- **Difference Analysis**: Identify variations between address records
- **Batch Comparison**: Process multiple comparison operations

### 🗄️ Database Integration
- **SQL Server/Azure SQL**: Direct database connectivity
- **Table & Query Modes**: Flexible data extraction options
- **Preview & Download**: Paginated results with download capabilities

### 🌐 Public API Interface
- **Interactive Documentation**: Accordion-based API explorer
- **Live Testing**: Test endpoints directly from the web interface
- **Sample Data**: Download sample files for API testing
- **No Authentication**: Simplified access for public endpoints

### 🗺️ Geographic Visualization
- **Interactive Mapping**: Leaflet-based geographic visualization
- **Regional Filtering**: Filter and analyze addresses by location
- **Marker Clustering**: Efficient display of multiple address points

## Configuration

### Environment Setup
Create a `.env` file in the backend directory with your Azure OpenAI credentials:
```env
CLIENT_ID=your_actual_client_id_here
CLIENT_SECRET=your_actual_client_secret_here
WSO2_AUTH_URL=https://api-test.cbre.com:443/token
AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
```

### Backend CLI Features
The backend includes a powerful CLI for address processing:

**Basic Usage:**
```bash
# Process a CSV file
python csv_address_processor.py input.csv

# Process single address
python csv_address_processor.py --address "123 Main St, New York, NY"

# Batch processing
python csv_address_processor.py --batch-process --base-dir "./backend"
```

**Advanced Options:**
- `--country UK`: Force specific country processing
- `--format json|formatted|detailed`: Output format options
- `--batch-size 10`: Control batch processing size
- `--compare "Address1" "Address2"`: Compare two addresses
- `--output results.csv`: Save results to file

## API Documentation

The application provides comprehensive API documentation through the **Public API** component. Visit the frontend interface and navigate to the "Public API" tab for:

- **Interactive API Testing**: Test all endpoints directly from the browser
- **Request/Response Examples**: See example requests and responses
- **Parameter Documentation**: Detailed parameter descriptions
- **Sample File Downloads**: Get sample files for testing uploads

## Development Notes

### Current Features
- ✅ File upload and processing (Excel/CSV)
- ✅ Single and batch address standardization
- ✅ Database connectivity (SQL Server/Azure SQL)
- ✅ File comparison and analysis
- ✅ Public API with comprehensive endpoints
- ✅ Interactive API documentation and testing
- ✅ Geographic visualization and mapping
- ✅ Sample file downloads for testing

### Architecture Highlights
- **Modular Design**: Clean separation between frontend and backend
- **Type Safety**: Full TypeScript implementation in frontend
- **State Management**: Redux Toolkit for predictable state updates
- **API Versioning**: Structured v1 API endpoints for stability
- **Error Handling**: Comprehensive error management throughout the stack

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with proper documentation
4. **Test thoroughly** using the provided API testing interface
5. **Submit a pull request** with detailed description

## License

[Add your license information here]

## Support and Documentation

For additional documentation and support:
- **Backend CLI Guide**: `chatbot-app/backend/README.md`
- **Frontend Component Guide**: `chatbot-app/frontend/README.md`
- **Quick Setup Guide**: `chatbot-app/QUICKSTART.md`
- **API Testing**: Use the Public API tab in the web interface

---

**AddressIQ** - Your comprehensive solution for intelligent address processing, standardization, and geographic analysis.