# AddressIQ Frontend

A React TypeScript application with Redux state management for handling file uploads and address processing.

## Features

- **File Upload Component**: Upload Excel files with progress tracking
- **Address Processing Component**: Process addresses in free text format
- **Redux State Management**: Using Redux Toolkit with Redux Observable epics
- **Routing**: React Router for navigation between components
- **TypeScript**: Full type safety throughout the application

## Project Structure

```
src/
├── components/         # React components
│   ├── FileUpload/       # File upload component
│   │   ├── FileUpload.tsx
│   │   ├── FileUpload.css
│   │   └── index.ts
│   ├── AddressProcessing/  # Address processing component
│   │   ├── AddressProcessing.tsx
│   │   ├── AddressProcessing.css
│   │   └── index.ts
│   ├── Chat.tsx          # Legacy chat component
│   ├── ChatInput.tsx     # Legacy chat input component
│   └── ChatMessage.tsx   # Legacy chat message component
├── store/              # Redux store configuration
│   ├── index.ts           # Store setup and configuration
│   ├── slices/           # Redux slices
│   │   ├── fileUploadSlice.ts
│   │   └── addressProcessingSlice.ts
│   └── epics/            # Redux Observable epics
│       ├── index.ts
│       ├── fileUploadEpic.ts
│       └── addressProcessingEpic.ts
├── services/           # API service layer
│   └── api.ts            # Axios API configurations
├── hooks/              # Custom React hooks
│   └── redux.ts          # Typed Redux hooks
├── types/              # TypeScript type definitions
│   └── index.ts
├── App.tsx             # Main app component with routing
├── App.css             # Global app styles
└── index.tsx           # Application entry point
```

## Components

### FileUpload Component
- **Location**: `/file-upload`
- **Files**: `src/components/FileUpload/`
- **Purpose**: Handles Excel file uploads (.xlsx, .xls)
- **Features**:
  - File type validation
  - Upload progress tracking
  - Success/error feedback
  - Navigation to Address Processing page

### AddressProcessing Component
- **Location**: `/address-processing`
- **Files**: `src/components/AddressProcessing/`
- **Purpose**: Processes addresses in free text format
- **Features**:
  - Free text address input
  - Address processing with API calls
  - Before/after address comparison
  - Copy to clipboard functionality
  - Navigation to File Upload page

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
   The application will run on http://localhost:3004

3. **Build for Production**
   ```bash
   npm run build
   ```

## Technologies Used

- **React 18** with TypeScript
- **Redux Toolkit** for state management
- **Redux Observable** for handling async operations
- **React Router** for routing
- **Axios** for API calls
- **RxJS** for reactive programming

## Navigation

The application provides seamless navigation between the two main features:
- From File Upload → Address Processing
- From Address Processing → File Upload

Each page includes a navigation link to switch between the two components.

## Styling

- Responsive design that works on desktop and mobile
- Clean, modern UI with consistent styling
- Loading states and progress indicators
- Success and error state feedback
- Hover effects and smooth transitions

## Error Handling

- File type validation for uploads
- Network error handling
- User-friendly error messages
- Loading states during API calls
- Progress tracking for file uploads
