# AddressIQ

A modern intelligent address processing application with advanced file upload, address standardization, and geographical visualization capabilities.

## Overview

AddressIQ is a full-stack web application that combines a React TypeScript frontend with a Python Flask backend to deliver comprehensive address intelligence solutions. The application provides file upload functionality, address processing capabilities, and interactive map visualization.

## Features

- **File Upload Interface**: Excel file upload with progress tracking and validation
- **Address Processing**: Advanced address standardization and processing capabilities
- **Interactive Map Visualization**: Geographic data visualization with Leaflet integration
- **Redux State Management**: Comprehensive state management with Redux Toolkit
- **Real-time Communication**: Seamless frontend-backend integration
- **Modern Tech Stack**: Built with the latest web technologies

## Architecture

### Frontend (`/frontend`)
- **React 18** with TypeScript
- **Tabbed Navigation**: Clean interface with File Upload, Address Processing, and Map View tabs
- **Redux Toolkit**: State management with Redux Observable epics
- **Responsive Design**: Works across desktop and mobile devices
- **API Integration**: Clean service layer for backend communication

### Backend (`/backend`)
- **Python Flask** application
- **Address Processing Engine**: Standardization and validation
- **RESTful API**: Clean endpoints for frontend communication
- **Modular Architecture**: Organized services and models

## Project Structure

```
AddressIQ/
 README.md
 QUICKSTART.md
 start-dev.sh
 frontend/                    # React TypeScript frontend
    package.json
    tsconfig.json
    README.md               # Frontend documentation
    build/                  # Production build output
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
- Excel file upload (.xlsx, .xls) with drag-and-drop support
- Real-time upload progress tracking
- File type validation and error handling
- Success/error feedback with user-friendly messages

### Address Processing Component
- Free text address input and processing
- Address standardization and validation
- Before/after address comparison
- Copy to clipboard functionality
- Real-time processing feedback

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
  - **Response**: `{ message: string }`

#### Address Processing
- **POST** `/api/process-address`
  - **Content-Type**: `application/json`
  - **Body**: `{ address: string }`
  - **Response**: `{ processedAddress: string }` or `{ message: string }`

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
2. **File Upload Failures**: Check file format (.xlsx, .xls) and size limits
3. **Module Not Found**: Run `npm install` in frontend and `pip install -r requirements.txt` in backend
4. **Port Conflicts**: Ensure ports 3003 and 5001 are available

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
- **Flask** web framework
- **Address processing libraries**
- **RESTful API design**

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

This project is licensed under the MIT License. See the LICENSE file for more details.

##  Recent Updates

-  Implemented tabbed navigation interface
-  Added file upload functionality with progress tracking
-  Created address processing and standardization features
-  Integrated interactive map visualization
-  Enhanced Redux state management architecture
-  Improved responsive design and user experience
-  Added comprehensive error handling and user feedback
-  Removed legacy chat components for focused functionality

---

**AddressIQ** - Intelligent address processing with comprehensive file handling and geographic visualization capabilities.
