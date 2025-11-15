# AddressIQ Frontend

A modern React TypeScript application providing a comprehensive user interface for intelligent address processing, file uploads, database connectivity, and API testing. Built with Redux state management and featuring an interactive map interface.

## Overview

The AddressIQ frontend is a single-page application that provides an intuitive interface for all address intelligence features. It includes multiple specialized components for different workflows, comprehensive state management, and a powerful API testing interface.

## Features

### Core Components
- **File Upload Component**: Upload Excel/CSV files with drag-and-drop, async processing, and progress tracking
- **Address Processing Component**: AI-powered address standardization with real-time processing
- **Compare Upload Component**: File comparison and analysis functionality with async processing
- **Database Connect Component**: Direct database connectivity with table/query modes and preview capabilities
- **Public API Component**: Interactive API documentation and testing interface with accordion UI
- **Region & City Map Component**: Interactive geographic visualization with Leaflet integration
- **Processing History Component**: Job tracking with filtering, status monitoring, and download management

### User Experience
- **Tabbed Navigation**: Seamless navigation between different application features
- **CBRE Green Theme**: Professional styling with #003f2d color scheme
- **Responsive Design**: Works across desktop and mobile devices
- **Real-time Feedback**: Progress indicators, status updates, and error handling
- **Smart File Management**: Automatic file availability detection with visual indicators
- **Status Indicators**: Clear visual feedback (Download/Expired/File Not Available)
- **Sample Downloads**: Built-in sample file downloads for testing

### Technical Features
- **Redux State Management**: Comprehensive state management with Redux Toolkit and Redux Observable (RxJS epics)
- **Async Processing**: Non-blocking file uploads with background job tracking and status polling
- **Automatic Cleanup**: Backend scheduler automatically deletes expired files daily at 2 AM
- **File Validation**: Client-side tracking of file availability with 404/410 error detection
- **TypeScript**: Full type safety throughout the application
- **API Integration**: Clean service layer for backend communication with async support
- **SQLite Job Tracking**: Persistent job history with automatic cleanup (7-day retention)
- **Error Handling**: User-friendly error messages with specific handling for expired/missing files
- **Performance Optimization**: Efficient rendering and state updates with map tile loading fixes

## Project Structure

The frontend is organized into a clear, modular structure:

```
frontend/
├── package.json                 # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
├── build/                      # Production build output
├── public/
│   └── index.html             # Main HTML template
└── src/
    ├── App.tsx                # Main application component with routing
    ├── App.css                # Global application styles
    ├── index.tsx              # Application entry point
    ├── index.css              # Global CSS styles
    ├── setupProxy.js          # Development proxy configuration
    ├── components/            # React components
    │   ├── FileUpload/        # File upload functionality
    │   │   ├── FileUpload.tsx
    │   │   ├── FileUpload.css
    │   │   └── index.ts
    │   ├── AddressProcessing/ # Address standardization
    │   │   ├── AddressProcessing.tsx
    │   │   ├── AddressProcessing.css
    │   │   └── index.ts
    │   ├── CompareUpload/     # File comparison features
    │   │   ├── CompareUpload.tsx
    │   │   ├── CompareUpload.css
    │   │   └── index.ts
    │   ├── DatabaseConnect/   # Database integration
    │   │   ├── DatabaseConnect.tsx
    │   │   ├── DatabaseConnect.css
    │   │   └── index.ts
    │   ├── PublicAPI/         # API documentation and testing
    │   │   ├── PublicAPI.tsx
    │   │   ├── PublicAPI.css
    │   │   └── index.ts
    │   ├── JobHistory/        # Processing history and job tracking
    │   │   ├── JobHistory.tsx
    │   │   ├── JobHistory.css
    │   │   └── index.ts
    │   └── RegionCityMap/     # Interactive map visualization
    │       ├── RegionCityMap.tsx
    │       ├── RegionCityMap.css
    │       └── index.ts
    ├── store/                 # Redux store configuration
    │   ├── index.ts          # Store setup and configuration
    │   ├── epics.ts          # RxJS epic configuration for async actions
    │   └── slices/           # Redux Toolkit slices
    │       ├── fileUploadSlice.ts
    │       ├── addressProcessingSlice.ts
    │       ├── compareUploadSlice.ts
    │       ├── databaseConnectSlice.ts
    │       ├── jobHistorySlice.ts
    │       └── mapSlice.ts
    ├── services/             # API service layer
    │   └── api.ts           # Axios configuration and API calls
    ├── hooks/               # Custom React hooks
    │   └── redux.ts         # Typed Redux hooks
    └── types/               # TypeScript type definitions
        └── index.ts         # Application-wide type definitions
```

## Component Overview

### 📁 File Upload Component
- **Purpose**: Upload Excel/CSV files for batch address processing
- **Features**: 
  - Drag-and-drop file selection
  - Async processing with background job tracking
  - Progress tracking with visual indicators
  - File validation (format, size)
  - Real-time processing status updates
  - Optional webhook notifications
  - User guidance messages
- **API Integration**: `/api/v1/files/upload-async` endpoint (with `/api/v1/files/status` polling)
- **State Management**: `fileUploadSlice.ts` with RxJS epic for status polling

### 🏠 Address Processing Component
- **Purpose**: Individual address standardization and processing
- **Features**:
  - Real-time address input and processing
  - AI-powered standardization results
  - Confidence scoring display
  - Copy-to-clipboard functionality
- **API Integration**: `/api/v1/addresses/standardize` endpoint
- **State Management**: `addressProcessingSlice.ts`

### 📊 Compare Upload Component
- **Purpose**: Upload and compare address datasets
- **Features**:
  - File comparison functionality with async processing
  - Difference analysis visualization
  - Side-by-side comparison views
  - Export comparison results
  - Background job tracking
  - User guidance messages
- **API Integration**: `/api/v1/compare/upload` endpoint (async processing supported)
- **State Management**: `compareUploadSlice.ts` with RxJS epic for status polling

### 🗄️ Database Connect Component
- **Purpose**: Direct database connectivity and processing
- **Features**:
  - Table and SQL query modes
  - Connection string configuration
  - Preview processed results with pagination
  - Download processed CSV files
  - Real-time processing logs
- **API Integration**: `/api/v1/database/connect` endpoint
- **State Management**: `databaseConnectSlice.ts`

### 🌐 Public API Component
- **Purpose**: Interactive API documentation and testing interface
- **Features**:
  - Accordion-based API explorer
  - Live endpoint testing
  - Request/response examples
  - Sample file downloads
  - No authentication required
- **API Integration**: All v1 API endpoints
- **State Management**: Local component state

### 🗺️ Region City Map Component
- **Purpose**: Interactive geographic visualization of address data
- **Features**:
  - Leaflet-based interactive mapping
  - Address marker clustering
  - Regional filtering capabilities
  - Zoom and pan functionality
  - Custom CBRE-styled markers
- **API Integration**: Geocoding and coordinate services
- **State Management**: `mapSlice.ts`

### 📋 Processing History Component
- **Purpose**: Track and manage all file processing jobs
- **Features**:
  - Full job history with filtering (all/completed/processing/failed)
  - 8-column table with status monitoring
  - Component source tracking (File Upload vs Compare Upload)
  - Expiration countdown (7-day retention)
  - Smart download management with three status indicators:
    - **Download** (green) - File available and not expired
    - **Expired** (gray, italic) - File passed 7-day retention (410 status)
    - **File Not Available** (red, italic) - File missing from server (404 status)
  - File existence validation on download attempts
  - Refresh functionality
  - Green-themed bordered table design
  - Inline status legend for user guidance
- **API Integration**: `/api/v1/files/jobs` and `/api/v1/files/download/<filename>` endpoints
- **State Management**: `jobHistorySlice.ts` with polling for active jobs and file availability tracking

## Setup and Development

### Prerequisites
- **Node.js** 16.0 or higher
- **npm** 8.0 or higher (comes with Node.js)
- **TypeScript** knowledge for development

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd chatbot-app/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3003
   - Development server with hot reload enabled

### Available Scripts

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject from Create React App (use with caution)
npm run eject

# Type checking
npx tsc --noEmit

# Lint code
npm run lint  # if configured
```

### Environment Configuration

Create a `.env` file in the frontend directory for environment-specific settings:
```env
REACT_APP_API_URL=http://localhost:5001
REACT_APP_VERSION=1.0.0
```

## Development Guidelines

### State Management
The application uses Redux Toolkit with Redux Observable for state management:

- **Store Configuration**: Centralized in `store/index.ts` with epic middleware
- **Slices**: Feature-based state slices for each component
- **RxJS Epics**: Configured in `store/epics.ts` for async processing workflows
- **Async Actions**: Redux Observable epics handle status polling and job tracking
- **Typed Hooks**: Custom hooks for type-safe Redux usage

#### Key State Slices
- **fileUploadSlice**: File upload state with async processing and status polling
- **compareUploadSlice**: Compare upload state with async processing
- **jobHistorySlice**: Job tracking state with filtering and pagination
- **addressProcessingSlice**: Single address processing state
- **databaseConnectSlice**: Database connection and processing state
- **mapSlice**: Map visualization state

### Component Architecture
- **Functional Components**: All components use React hooks
- **TypeScript**: Full type safety with interfaces and types
- **CSS Modules**: Component-specific styling with CSS files
- **Error Boundaries**: Comprehensive error handling

### API Integration
- **Axios Client**: Configured in `services/api.ts`
- **Proxy Setup**: Development proxy in `setupProxy.js`
- **Error Handling**: Consistent error handling across all API calls
- **Response Types**: TypeScript interfaces for all API responses

#### Key API Methods
- **uploadFileAsync**: Async file upload with processing_id return
- **checkJobStatus**: Poll job status by processing_id
- **getJobHistory**: Retrieve job history with filtering options
- **downloadJobResult**: Download completed job files
- **getAdminStats**: Retrieve job statistics and metrics

### Styling Guidelines
- **CBRE Theme**: Primary color #003f2d (CBRE green)
- **Responsive Design**: Mobile-first approach
- **CSS Variables**: Consistent color and spacing variables
- **Component Styling**: Individual CSS files for each component

## Technologies Used

### Core Technologies
- **React 18**: Latest React with concurrent features and improved performance
- **TypeScript**: Full type safety with strict mode enabled
- **Redux Toolkit**: Modern Redux with Redux Toolkit Query for API state management
- **React Hooks**: Functional components with useState, useEffect, useContext
- **CSS3**: Modern styling with custom properties and flexbox/grid layouts

### Key Dependencies
- **Redux Toolkit**: `@reduxjs/toolkit` - Modern Redux development
- **React-Redux**: `react-redux` - React bindings for Redux
- **Redux Observable**: `redux-observable` - Handle complex async flows
- **Axios**: `axios` - Promise-based HTTP client for API calls
- **React Leaflet**: `react-leaflet` - Interactive maps with Leaflet integration
- **Country-State-City**: Geographic data for region filtering

### Development Dependencies
- **Create React App**: Project scaffolding and build tools
- **TypeScript**: Static type checking and IntelliSense
- **ESLint**: Code linting and quality checks
- **Web Vitals**: Performance monitoring for Core Web Vitals

## Testing

### Component Testing
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Generate coverage report
npm test -- --coverage
```

### Manual Testing
Use the Public API component to test all backend endpoints:
1. Navigate to the "Public API" tab
2. Use the accordion interface to explore endpoints
3. Download sample files for testing
4. Test endpoints with real data

## Build and Deployment

### Production Build
```bash
# Create optimized production build
npm run build

# The build folder contains the optimized static files
# Ready for deployment to any static hosting service
```

### Deployment Options
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **CDN Deployment**: AWS CloudFront, Azure CDN
- **Traditional Hosting**: Any web server capable of serving static files

### Performance Optimization
- **Code Splitting**: Automatic with Create React App
- **Tree Shaking**: Unused code elimination
- **Bundle Analysis**: Use `npm run build` to analyze bundle size
- **Lazy Loading**: Components loaded on demand

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Kill process using port 3003
npx kill-port 3003

# Or start on different port
PORT=3004 npm start
```

**2. API Connection Issues**
- Verify backend is running on port 5001
- Check proxy configuration in `setupProxy.js`
- Confirm CORS settings in backend

**3. TypeScript Errors**
```bash
# Type check without emitting files
npx tsc --noEmit

# Install missing type definitions
npm install @types/package-name
```

**4. Build Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Contributing

### Development Workflow
1. **Create feature branch**: `git checkout -b feature/component-name`
2. **Follow TypeScript conventions**: Use proper typing for all components
3. **Update tests**: Add tests for new components or functionality
4. **Check build**: Ensure `npm run build` works without errors
5. **Submit PR**: Include description of changes and testing performed

### Code Standards
- **TypeScript**: Strict mode enabled, no implicit any
- **ESLint**: Follow configured linting rules
- **Prettier**: Use consistent code formatting
- **Component Structure**: Follow established patterns for new components

## Architecture Decisions

### Why Redux Toolkit?
- **Predictable State**: Centralized state management
- **DevTools**: Excellent debugging capabilities
- **TypeScript Support**: Built-in TypeScript integration
- **Performance**: Optimized updates with Immer

### Why Accordion UI for Public API?
- **Organized Display**: Clean presentation of multiple endpoints
- **Interactive Testing**: Direct testing without external tools
- **User-Friendly**: Intuitive interface for developers
- **Self-Documenting**: Examples and responses built-in

### Why Leaflet for Mapping?
- **Open Source**: No licensing costs
- **Customizable**: Full control over map appearance
- **Performance**: Efficient rendering of multiple markers
- **Plugin Ecosystem**: Rich set of available plugins

## License

[Add your license information here]

## Support

For frontend-specific issues and questions:
- **Component Documentation**: Refer to individual component files
- **TypeScript Issues**: Check type definitions in `types/index.ts`
- **Build Problems**: Review Create React App documentation
- **State Management**: Review Redux Toolkit documentation

---

**AddressIQ Frontend** - Modern React TypeScript interface for comprehensive address intelligence and processing.