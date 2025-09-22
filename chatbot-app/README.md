# AddressIQ

A modern intelligent address processing application with advanced file upload, address standardization, database connectivity, and geographical visualization capabilities.

## Overview

AddressIQ is a comprehensive full-stack web application that combines a React TypeScript frontend with a Python Flask backend to deliver intelligent address processing solutions. The application provides multiple processing modes, public API endpoints, database integration, and interactive geographic visualization.

## Features

### Core Functionality
- **File Upload & Processing**: Excel/CSV file upload with drag-and-drop functionality and batch processing
- **Address Standardization**: AI-powered address processing with single and batch modes
- **Database Integration**: Direct SQL Server/Azure SQL connectivity with table/query modes
- **File Comparison**: Upload and compare address datasets with analysis tools
- **Public API Interface**: Interactive API documentation and testing with accordion UI
- **Geographic Visualization**: Interactive map visualization with Leaflet integration

### Technical Features
- **RESTful API v1**: Comprehensive endpoints for programmatic access
- **Redux State Management**: Comprehensive state management with Redux Toolkit
- **Real-time Processing**: Live updates and progress tracking
- **Sample Downloads**: Built-in sample files for testing and development
- **CBRE Branding**: Professional green theme with modern styling
- **No Authentication Required**: Simplified access for public API endpoints

### Backend CLI Tools
- **CSV Processing**: Advanced command-line tools for address processing
- **Batch Operations**: Process multiple files with batch processing modes
- **Address Comparison**: Compare addresses and analyze differences
- **Direct Input Processing**: Process individual addresses from command line

## Architecture

### Frontend (`/frontend`)
- **React 18** with TypeScript for modern component-based architecture
- **Redux Toolkit** with Redux Observable for comprehensive state management
- **Component Structure**:
  - **File Upload**: Excel/CSV file processing with drag-and-drop functionality
  - **Address Processing**: Real-time individual address standardization
  - **Compare Upload**: File comparison and analysis functionality
  - **Database Connect**: Table/Query mode with preview and download capabilities
  - **Public API**: Interactive API documentation and testing interface with accordion UI
  - **Region City Map**: Interactive geographic visualization with Leaflet
- **CBRE Theme**: Professional green styling (#003f2d) with responsive design
- **API Integration**: Axios-based service layer with development proxy configuration

### Backend (`/backend`)
- **Python Flask** application with modular architecture
- **Azure OpenAI Integration** through WSO2 gateway with OAuth2 authentication
- **Address Processing Engine**: AI-powered standardization with confidence scoring
- **RESTful API v1**: Comprehensive endpoints including:
  - `/api/v1/files/upload` - File upload and processing
  - `/api/v1/addresses/standardize` - Single address standardization
  - `/api/v1/addresses/batch-standardize` - Batch address processing
  - `/api/v1/compare/upload` - File comparison processing
  - `/api/v1/database/connect` - Database connection and processing
  - `/api/v1/samples/*` - Sample file downloads
- **Database Support**: SQL Server/Azure SQL connectivity with table/query modes
- **CLI Tools**: Powerful command-line interface for batch processing and address operations

## Quick Start

### Prerequisites
- **Node.js** 16+ and npm (for frontend)
- **Python** 3.8+ and pip (for backend)
- **SQL Server** or **Azure SQL Database** (optional, for database features)

### Development Setup

1. **Clone and navigate to the project**
   ```bash
   git clone https://github.com/anilmalik13/AddressIQ.git
   cd AddressIQ/chatbot-app
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   
   # Create .env file with your Azure OpenAI credentials
   # CLIENT_ID=your_client_id_here
   # CLIENT_SECRET=your_client_secret_here
   # WSO2_AUTH_URL=https://api-test.cbre.com:443/token
   # AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
   
   python run.py
   ```

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access the Application**
   - **Frontend**: http://localhost:3003
   - **Backend API**: http://localhost:5001
   - **API Documentation**: http://localhost:3003 (Public API tab)

### Using the Quick Start Script
```bash
# Use the provided development script (Linux/macOS)
./start-dev.sh

# Or start services individually as shown above
```

## Application Features

### 📁 File Upload & Processing
- **Multi-format Support**: Excel (.xlsx, .xls) and CSV file processing
- **Drag-and-Drop Interface**: Intuitive file selection with visual feedback
- **Progress Tracking**: Real-time upload and processing status indicators
- **Batch Processing**: Handle large datasets efficiently with configurable batch sizes
- **File Validation**: Automatic format and size validation

### 🏠 Address Standardization
- **AI-Powered Processing**: Azure OpenAI integration for intelligent address parsing
- **Single & Batch Modes**: Process individual addresses or multiple addresses
- **Confidence Scoring**: Quality assessment for processed addresses
- **Global Support**: Multi-country address standardization capabilities
- **Real-time Results**: Instant processing with copy-to-clipboard functionality

### 📊 Compare & Analysis
- **File Comparison**: Upload and compare address datasets
- **Difference Analysis**: Identify variations between address records
- **Side-by-side Views**: Visual comparison interface
- **Export Results**: Download comparison analysis results

### 🗄️ Database Integration
- **SQL Server/Azure SQL**: Direct database connectivity
- **Table & Query Modes**: Flexible data extraction options
- **Connection String Support**: Secure database authentication
- **Preview Functionality**: Paginated results with download capabilities
- **Processing Logs**: Real-time processing status and detailed logs

### 🌐 Public API Interface
- **Interactive Documentation**: Accordion-based API explorer
- **Live Testing**: Test endpoints directly from the web interface
- **Request/Response Examples**: Comprehensive API documentation
- **Sample Downloads**: Built-in sample files for testing
- **No Authentication**: Simplified access for public endpoints

### 🗺️ Geographic Visualization
- **Interactive Mapping**: Leaflet-based geographic visualization
- **Address Markers**: Visual representation of processed addresses
- **Regional Filtering**: Filter and analyze addresses by location
- **Zoom & Pan**: Full map interaction capabilities

## Project Structure

```
chatbot-app/
├── README.md                    # This file - application overview
├── QUICKSTART.md               # Quick setup guide
├── start-dev.sh                # Development startup script
├── frontend/                   # React TypeScript frontend
│   ├── package.json           # Frontend dependencies and scripts
│   ├── tsconfig.json          # TypeScript configuration
│   ├── README.md              # Frontend-specific documentation
│   ├── build/                 # Production build output
│   ├── public/                # Static files and HTML template
│   └── src/                   # Source code
│       ├── App.tsx            # Main application component with routing
│       ├── components/        # React components
│       │   ├── FileUpload/    # File upload functionality
│       │   ├── AddressProcessing/ # Address standardization
│       │   ├── CompareUpload/ # File comparison features
│       │   ├── DatabaseConnect/ # Database integration
│       │   ├── PublicAPI/     # API documentation and testing interface
│       │   └── RegionCityMap/ # Interactive map visualization
│       ├── store/             # Redux store configuration
│       ├── services/          # API service layer
│       ├── hooks/             # Custom React hooks
│       └── types/             # TypeScript type definitions
└── backend/                   # Python Flask backend
    ├── README.md              # Backend-specific documentation
    ├── requirements.txt       # Python dependencies
    ├── run.py                 # Application entry point
    ├── app/                   # Flask application
    │   ├── main.py           # Main Flask app with API routes
    │   ├── config/           # Configuration files
    │   ├── models/           # Data models
    │   └── services/         # Business logic services
    ├── inbound/              # File upload directory
    ├── outbound/             # Processed file output
    ├── archive/              # Archived files
    ├── samples/              # Sample files for API testing
    └── CSV processing tools  # CLI utilities for address processing
```
## API Documentation

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/files/upload` | POST | Upload Excel/CSV files for processing |
| `/api/v1/addresses/standardize` | POST | Standardize a single address |
| `/api/v1/addresses/batch-standardize` | POST | Standardize multiple addresses |
| `/api/v1/compare/upload` | POST | Upload files for comparison analysis |
| `/api/v1/database/connect` | POST | Connect to database and process addresses |
| `/api/v1/samples/file-upload` | GET | Download sample upload file |
| `/api/v1/samples/compare-upload` | GET | Download sample compare file |

### Example API Usage

**Single Address Standardization:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"address": "123 Main St, New York, NY 10001"}' \
  http://localhost:5001/api/v1/addresses/standardize
```

**File Upload:**
```bash
curl -X POST -F "file=@addresses.xlsx" \
  http://localhost:5001/api/v1/files/upload
```

**Database Connection:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"server": "localhost", "database": "addresses_db", "query": "SELECT address FROM customers LIMIT 100"}' \
  http://localhost:5001/api/v1/database/connect
```

For complete API documentation and interactive testing, visit the **Public API** tab in the web interface.

## Backend CLI Usage

The backend includes powerful command-line tools for address processing:

### Basic Commands

```bash
# Process a CSV file
python csv_address_processor.py input.csv

# Process single address
python csv_address_processor.py --address "123 Main St, New York, NY"

# Process multiple addresses
python csv_address_processor.py --address "123 Main St" "456 Oak Ave" "789 Park Blvd"
```

### Advanced Features

```bash
# Batch processing with custom directory
python csv_address_processor.py --batch-process --base-dir "./backend"

# Address comparison
python csv_address_processor.py --compare "123 Main St, NYC" "123 Main Street, New York"

# Custom output formats
python csv_address_processor.py input.csv --format json --output results.json

# Force specific country processing
python csv_address_processor.py --address "123 High St, London" --country "UK"
```

### CLI Options
- `--batch-process`: Process all files in inbound directory
- `--batch-compare`: Process comparison files in batch
- `--address "text"`: Process individual addresses
- `--compare "addr1" "addr2"`: Compare two addresses
- `--country CODE`: Force specific country processing
- `--format json|formatted|detailed`: Output format
- `--output filename`: Save results to file
- `--batch-size N`: Control batch processing size
- `--no-free-apis`: Disable free API fallbacks
- `--test-apis`: Test API connectivity
- `--db-stats`: Generate database statistics

## Technologies Used

### Frontend Technologies
- **React 18** with TypeScript for modern component architecture
- **Redux Toolkit** with Redux Observable for state management
- **React Leaflet** for interactive mapping
- **Axios** for HTTP client communication
- **CSS3** with CBRE green theme (#003f2d)

### Backend Technologies
- **Python 3.11+** with Flask web framework
- **Azure OpenAI SDK** for AI-powered address processing
- **WSO2 Gateway** for secure API access
- **Pandas** for data manipulation
- **pyodbc** for SQL Server/Azure SQL connectivity
- **Flask-CORS** for cross-origin resource sharing

### Development Tools
- **TypeScript** for type safety
- **npm/Node.js** for frontend package management
- **Python Virtual Environment** for dependency isolation
- **Git** for version control

## Configuration

### Environment Variables
Create a `.env` file in the backend directory:
```env
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
WSO2_AUTH_URL=https://api-test.cbre.com:443/token
AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
```

### Database Connection Strings
**SQL Server:**
```
Server=your_server;Database=your_database;Trusted_Connection=yes;
```

**Azure SQL:**
```
Server=tcp:yourserver.database.windows.net,1433;Database=yourdatabase;User ID=username;Password=password;
```

## Development Guidelines

### Frontend Development
- **Component Structure**: Follow the established pattern with .tsx, .css, and index.ts files
- **State Management**: Use Redux slices for component-specific state
- **TypeScript**: Maintain strict type safety throughout
- **Testing**: Add tests for new components and functionality

### Backend Development
- **API Endpoints**: Add new routes in `app/main.py`
- **Business Logic**: Implement services in `app/services/`
- **Configuration**: Update settings in `app/config/`
- **CLI Tools**: Extend existing CLI functionality as needed

### Best Practices
- **Error Handling**: Comprehensive error management throughout the stack
- **Performance**: Optimize for large file processing and batch operations
- **Security**: Secure handling of database connections and file uploads
- **Documentation**: Keep README files updated with new features

## Troubleshooting

### Common Issues

**1. Port Conflicts**
```bash
# Kill process using port 3003 (frontend)
npx kill-port 3003

# Kill process using port 5001 (backend)
npx kill-port 5001
```

**2. Python Environment Issues**
```bash
# Recreate virtual environment
cd backend
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**3. Node.js Issues**
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**4. Database Connection Problems**
- Verify connection string format
- Check network connectivity
- Validate user permissions
- Test with SQL Server Management Studio

### Performance Tips
- **File Size**: Keep upload files under 50MB for optimal performance
- **Batch Size**: Adjust batch processing size based on system resources
- **Memory Usage**: Monitor memory usage during large file processing
- **API Limits**: Be aware of Azure OpenAI rate limits

## License

[Add your license information here]

## Support

For technical support:
- **Frontend Issues**: Check `frontend/README.md`
- **Backend Issues**: Check `backend/README.md`
- **API Documentation**: Use the Public API tab in the web interface
- **CLI Help**: Run `python csv_address_processor.py --help`

---

**AddressIQ** - Comprehensive address intelligence platform with AI-powered processing, database integration, and interactive visualization.
    public/
       index.html
    src/
        App.tsx             # Main app component with tabbed navigation
        App.css             # Global styles
        index.tsx           # Application entry point
        index.css           # Global CSS styles
        setupProxy.js       # Proxy configuration for API calls
        components/         # React components
           FileUpload/     # File upload feature
              FileUpload.tsx
              FileUpload.css
              index.ts
           AddressProcessing/ # Address processing feature
              AddressProcessing.tsx
              AddressProcessing.css
              index.ts
           RegionCityMap/  # Interactive map visualization
               RegionCityMap.tsx
               RegionCityMap.css
               index.ts
        store/              # Redux store setup
           index.ts        # Store configuration
           slices/         # Redux slices
              fileUploadSlice.ts
              addressProcessingSlice.ts
           epics/          # Redux Observable epics
               index.ts
               fileUploadEpic.ts
               addressProcessingEpic.ts
        services/           # Axios API configuration
           api.ts
        hooks/              # Typed Redux hooks
           redux.ts
        types/              # TypeScript type definitions
            index.ts
 backend/                    # Python backend
     requirements.txt
     run.py
     example_address_standardization.py
     ADDRESS_STANDARDIZATION_README.md
     app/
         main.py
         config/
         models/
         services/
```

##  Quick Start

**Option 1: Use the automated setup script**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

**Option 2: Manual setup (see detailed instructions below)**

##  Prerequisites

- **Node.js** (v14 or higher) and npm
- **Python 3.7+**
- **Azure OpenAI** account (if using AI features)

##  Environment Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd AddressIQ
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
python run.py
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

##  Features

### File Upload Component
- Excel/CSV file upload (.xlsx, .xls, .csv) with drag-and-drop support
- Real-time upload progress tracking
- File type validation and error handling
- Success/error feedback with user-friendly messages
- File storage in secure directory with timestamp naming

### Address Processing Component
- Free text address input and processing
- AI-powered address standardization with Azure OpenAI integration
- Graceful fallback to free geocoding APIs (Nominatim, Geocodify)
- Before/after address comparison with confidence scoring
- Copy to clipboard functionality
- Real-time processing feedback with detailed component breakdown

### Interactive Map Visualization
- Interactive maps using Leaflet and React-Leaflet
- Region and country selection interface
- Coordinate plotting and visualization
- Geographic data integration with Country-State-City library
- Custom map markers and popups

### Technical Features
- **Redux State Management**: Comprehensive state management with Redux Toolkit
- **Redux Observable**: Reactive programming for async operations
- **TypeScript**: Full type safety throughout the application
- **Responsive Design**: Modern UI that works on all devices
- **Tabbed Navigation**: Clean interface for switching between features
- **Error Handling**: Comprehensive error management and user feedback

##  API Endpoints

### Backend API

#### File Upload
- **POST** `/api/upload-excel`
  - **Content-Type**: `multipart/form-data`
  - **Body**: FormData with file field
  - **Response**: `{ message: string, file_path: string, filename: string, file_info: object }`

#### List Uploaded Files
- **GET** `/api/uploaded-files`
  - **Response**: `{ files: array }` with file metadata

#### Address Processing
- **POST** `/api/process-address`
  - **Content-Type**: `application/json`
  - **Body**: `{ address: string }`
  - **Response**: `{ processedAddress: string, confidence: string, components: object, status: string, source: string }`

#### Geographic Data
- **GET** `/api/coordinates`
  - **Query Parameters**: `region`, `country`
  - **Response**: Coordinate data for the specified region and country

##  Usage

1. Start both frontend and backend servers
2. Navigate to `http://localhost:3003`
3. Use the tabbed interface to access different features:
   - **File Upload**: Upload Excel files for processing
   - **Address Processing**: Enter addresses for standardization
   - **Map View**: Visualize geographic data and coordinates

### Example Use Cases
- Upload customer address lists for standardization
- Process individual addresses for validation
- Visualize address data on interactive maps
- Export processed address data

##  Troubleshooting

### Common Issues
1. **CORS Errors**: Ensure Flask-CORS is installed and configured
2. **File Upload Failures**: Check file format (.xlsx, .xls, .csv) and size limits (50MB max)
3. **Module Not Found**: Run `npm install` in frontend and `pip install -r requirements.txt` in backend
4. **Port Conflicts**: Ensure ports 3003 and 5001 are available
5. **Azure OpenAI Issues**: Check credentials or rely on free API fallback

### Debug Mode
The application includes extensive logging. Check the console output for:
- File upload progress and status
- Address processing results
- API request/response details
- Error messages with stack traces

## Technologies Used

### Frontend
- **React 18** with TypeScript
- **Redux Toolkit** for state management
- **Redux Observable** for handling async operations
- **Leaflet & React-Leaflet** for interactive maps
- **Axios** for API calls
- **Country-State-City** library for geographical data

### Backend
- **Python 3.11+**
- **Flask** web framework with CORS support
- **Pandas & OpenPyXL** for Excel/CSV processing
- **Azure OpenAI** integration with OAuth2 authentication
- **Free geocoding APIs** (Nominatim, Geocodify) for fallback
- **Werkzeug** for secure file handling

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

This project is licensed under the MIT License. See the LICENSE file for more details.

##  Recent Updates

-  Implemented comprehensive file upload API for Excel/CSV processing
-  Added AI-powered address standardization with Azure OpenAI integration
-  Created graceful fallback to free geocoding APIs
-  Enhanced file validation and secure storage with timestamp naming
-  Implemented tabbed navigation interface
-  Integrated interactive map visualization
-  Enhanced Redux state management architecture
-  Improved responsive design and user experience
-  Added comprehensive error handling and user feedback
-  Removed legacy chat components for focused functionality
-  Added support for CSV files in addition to Excel formats

---

**AddressIQ** - Intelligent address processing with comprehensive file handling and geographic visualization capabilities.
