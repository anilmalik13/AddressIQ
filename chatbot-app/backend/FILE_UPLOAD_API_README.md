# File Upload API Documentation

## Overview
The AddressIQ backend provides comprehensive file upload functionality to handle Excel (.xlsx, .xls) and CSV files containing address data. Files are uploaded to the application's `inbound/` directory under `chatbot-app/backend` with timestamp-based naming to prevent conflicts. Processed output is written to `outbound/`. The system includes AI-powered address processing with graceful fallback to free geocoding APIs.

## New API Endpoints
- **Content-Type**: `multipart/form-data`
  - `file`: The file to upload (Excel or CSV format)
- **Response**: 
  ```json
  "message": "File uploaded successfully! Processing started.",
  "processing_id": "proc_20250827_123456_1234",
    "message": "File uploaded successfully! File contains X rows with Y columns.",
    "file_path": "C:\\uploaded_files\\filename_20250811_143022.xlsx",
    "filename": "filename_20250811_143022.xlsx",
    "file_info": {
      "rows": 100,
      "columns": 5,
      "column_names": ["name", "address", "city", "state", "zip"]
    }
  }
  ```
- **Endpoint**: `POST /api/process-address`
- **Content-Type**: `application/json`
- **Body**: 
  ```json
  {
    "address": "123 Main St, New York, NY 10001"
  }
    "path": "inbound/addresses_20250811_143022.xlsx"
- **Response**: 
  ```json
  {
    "processedAddress": "123 Main Street, New York, NY 10001-1234",
    "confidence": "high",
    "components": {
- **Endpoint**: `GET /api/processing-status/<processing_id>`
- **Response**: `{ status, progress, message, output_file? }`

### 4. Get Processing Logs
- **Endpoint**: `GET /api/processing-status/<processing_id>/logs`
- **Response**: `{ logs: [{ ts, message, progress? }] }`
      "street_number": "123",
      "street_name": "Main Street",
### 5. Get Coordinates (Placeholder)
      "state": "NY",
      "postal_code": "10001-1234",
### Upload/Output Directories
- Inbound location: `<repo>/chatbot-app/backend/inbound`
- Outbound location: `<repo>/chatbot-app/backend/outbound`
- Files are automatically renamed with timestamps to prevent conflicts
- Format: `{original_name}_{YYYYMMDD_HHMMSS}.{extension}`
    },
    "status": "success",
    "source": "azure_openai"
  }
  ```

### 3. List Uploaded Files
- **Endpoint**: `GET /api/uploaded-files`
- **Response**: 
  ```json
  {
    "files": [
      {
        "filename": "addresses_20250811_143022.xlsx",
        "size": 25600,
        "modified": "2025-08-11T14:30:22",
        "path": "C:\\uploaded_files\\addresses_20250811_143022.xlsx"
      }
    ]
  }
  ```

### 4. Get Coordinates (Placeholder)
- **Endpoint**: `GET /api/coordinates?region=NY&country=US`
- **Response**: 
  ```json
  {
    "region": "NY",
    "country": "US",
    "latitude": 0.0,
    "longitude": 0.0,
    "message": "Coordinate lookup functionality to be implemented"
  }
  ```

## File Upload Configuration

### Supported File Types
- Excel files: `.xlsx`, `.xls`
- CSV files: `.csv`

### File Size Limits
- Maximum file size: 50MB
- Configuration: `app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024`

### Upload Directory
- Default location: `C:\uploaded_files`
- Files are automatically renamed with timestamps to prevent conflicts
- Format: `{original_name}_{YYYYMMDD_HHMMSS}.{extension}`

## Dependencies Added

The following packages were added to `requirements.txt`:
- `werkzeug==2.3.7` - For secure filename handling
- `openpyxl==3.1.2` - For Excel file reading support

## Security Features

1. **File Type Validation**: Only allowed file extensions are accepted
2. **Secure Filename**: Uses `werkzeug.utils.secure_filename()` to prevent path traversal
3. **File Size Limits**: Prevents oversized file uploads
4. **Content Validation**: Attempts to read and validate file content before saving

## Error Handling

The API provides detailed error messages for common scenarios:
- No file provided
- Invalid file type
- File size too large
- Corrupted or invalid file format
- Processing errors

## Testing

A test script `test_file_upload.py` is provided to test all new endpoints:

```bash
cd backend
python test_file_upload.py
```

## Frontend Integration

The frontend `api.ts` service has been updated with:
- Enhanced error handling
- Progress tracking for file uploads
- Support for the new response formats
- Additional utility functions

## Usage Examples

### Frontend (TypeScript)
```typescript
import { uploadExcelFile, processAddress, getUploadedFiles } from './services/api';

// Upload file
const file = document.getElementById('file-input').files[0];
const result = await uploadExcelFile(file, (progress) => {
  console.log(`Upload progress: ${progress}%`);
});

// Process address
const result = await processAddress("123 Main St, NY");
console.log(result.processedAddress);
console.log(result.components);

// Get uploaded files
const files = await getUploadedFiles();
console.log(files);
```

### Python Backend Testing
```python
import requests

# Upload file
with open('test.xlsx', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5001/api/upload-excel', files=files)
    print(response.json())

# Process address
data = {'address': '123 Main St, New York, NY'}
response = requests.post('http://localhost:5001/api/process-address', json=data)
print(response.json())
```

## Next Steps

1. **File Processing**: Integrate with the existing `CSVAddressProcessor` to actually process uploaded files
2. **Batch Processing**: Add endpoints to process entire uploaded files
3. **Results Storage**: Store processing results and make them downloadable
4. **Progress Tracking**: Add real-time progress updates for batch processing
5. **File Management**: Add endpoints to delete or manage uploaded files
