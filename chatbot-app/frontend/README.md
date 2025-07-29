# AddressIQ Frontend

A React TypeScript application with Redux state management for intelligent address processing. This frontend provides a comprehensive solution for file uploads, address processing, and geographical visualization through an interactive map interface.

## Features

- **File Upload Component**: Upload Excel files with progress tracking and validation
- **Address Processing Component**: Process addresses in free text format with standardization
- **Region & City Map View**: Interactive map visualization with geographical data
- **Redux State Management**: Using Redux Toolkit with Redux Observable epics for async operations
- **Tabbed Navigation**: Seamless navigation between different application views
- **TypeScript**: Full type safety throughout the application

## Project Structure

The frontend is located in the `frontend/` directory of the AddressIQ project:

```
AddressIQ/
├── README.md
├── QUICKSTART.md
├── start-dev.sh
├── frontend/                    # React TypeScript frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── build/                   # Production build output
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.tsx              # Main app component with tabbed navigation
│       ├── App.css              # Global styles
│       ├── index.tsx            # Application entry point
│       ├── index.css            # Global CSS styles
│       ├── setupProxy.js        # Proxy configuration for API calls
│       ├── components/          # React components
│       │   ├── FileUpload/      # File upload feature
│       │   │   ├── FileUpload.tsx
│       │   │   ├── FileUpload.css
│       │   │   └── index.ts
│       │   ├── AddressProcessing/ # Address processing feature
│       │   │   ├── AddressProcessing.tsx
│       │   │   ├── AddressProcessing.css
│       │   │   └── index.ts
│       │   └── RegionCityMap/   # Interactive map visualization
│       │       ├── RegionCityMap.tsx
│       │       ├── RegionCityMap.css
│       │       └── index.ts
│       ├── store/               # Redux store setup
│       │   ├── index.ts         # Store configuration
│       │   ├── slices/          # Redux slices
│       │   │   ├── fileUploadSlice.ts
│       │   │   └── addressProcessingSlice.ts
│       │   └── epics/           # Redux Observable epics
│       │       ├── index.ts
│       │       ├── fileUploadEpic.ts
│       │       └── addressProcessingEpic.ts
│       ├── services/            # Axios API configuration
│       │   └── api.ts
│       ├── hooks/               # Typed Redux hooks
│       │   └── redux.ts
│       └── types/               # TypeScript type definitions
│           └── index.ts
└── backend/                     # Python backend
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

## Components

### FileUpload Component
- **Tab**: `File Upload`
- **Files**: `src/components/FileUpload/`
- **Purpose**: Handles Excel file uploads (.xlsx, .xls)
- **Features**:
  - File type validation
  - Upload progress tracking
  - Success/error feedback
  - Integration with Redux store

### AddressProcessing Component
- **Tab**: `Address Processing`
- **Files**: `src/components/AddressProcessing/`
- **Purpose**: Processes addresses in free text format
- **Features**:
  - Free text address input
  - Address standardization and processing
  - Before/after address comparison
  - Copy to clipboard functionality
  - Real-time processing feedback

### RegionCityMap Component
- **Tab**: `Map View`
- **Files**: `src/components/RegionCityMap/`
- **Purpose**: Interactive geographical visualization
- **Features**:
  - Interactive map using Leaflet and React-Leaflet
  - Region and country selection
  - Coordinate plotting and visualization
  - Geographic data integration
  - Custom map markers and popups

## Redux Store Architecture

### State Structure
```typescript
interface RootState {
    fileUpload: FileUploadState;
    addressProcessing: AddressProcessingState;
}
```

### File Upload State
```typescript
interface FileUploadState {
    uploading: boolean;
    uploadProgress: number;
    uploadResult: string | null;
    error: string | null;
}
```

### Address Processing State
```typescript
interface AddressProcessingState {
    processing: boolean;
    originalAddress: string;
    processedAddress: string | null;
    error: string | null;
}
```

## API Endpoints

The application expects the following backend API endpoints:

### File Upload
- **Endpoint**: `POST /api/upload-excel`
- **Content-Type**: `multipart/form-data`
- **Body**: FormData with file field
- **Response**: `{ message: string }`

### Address Processing
- **Endpoint**: `POST /api/process-address`
- **Content-Type**: `application/json`
- **Body**: `{ address: string }`
- **Response**: `{ processedAddress: string }` or `{ message: string }`

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```
   The application will run on http://localhost:3003

3. **Build for Production**
   ```bash
   npm run build
   ```

## Project Configuration

- **Port**: The development server runs on port 3003 (configured in package.json)
- **Proxy**: API calls are proxied to the backend via setupProxy.js configuration
- **TypeScript**: Configured with tsconfig.json for strict type checking

## Technologies Used

- **React 18** with TypeScript
- **Redux Toolkit** for state management
- **Redux Observable** for handling async operations
- **Leaflet & React-Leaflet** for interactive maps
- **Axios** for API calls
- **RxJS** for reactive programming
- **Country-State-City** library for geographical data

## Navigation

The application uses a tabbed interface for navigation between three main views:
- **File Upload**: Upload and process Excel files
- **Address Processing**: Standardize and process individual addresses
- **Map View**: Visualize geographical data and coordinates

Each component is accessible through the navigation tabs in the header, providing a seamless user experience.

## Styling

- Responsive design that works on desktop and mobile devices
- Clean, modern UI with consistent styling across all components
- Tabbed navigation interface with active state indicators
- Loading states and progress indicators for all async operations
- Success and error state feedback with clear messaging
- Interactive map styling with custom markers and popups
- Hover effects and smooth transitions throughout the application

## Error Handling

- File type validation for uploads
- Network error handling
- User-friendly error messages
- Loading states during API calls
- Progress tracking for file uploads
