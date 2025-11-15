# AddressIQ Backend

A powerful Python Flask backend providing comprehensive address intelligence services through RESTful APIs, CLI tools, and database integration capabilities.

## Overview

The AddressIQ backend serves as the core processing engine for address standardization, file processing, and data management. It combines Azure OpenAI integration, database connectivity, and flexible CLI tools to deliver enterprise-grade address intelligence solutions.

## Features

### API Endpoints (v1)
- **Async File Processing**: Upload files with asynchronous background processing and job tracking
- **Job Management**: Track processing jobs with status monitoring and 7-day retention
- **File Processing**: Upload and process Excel/CSV files for batch address standardization
- **File Download Validation**: Download endpoint checks file expiration (410) and existence (404) before serving files
- **Address Standardization**: Single and batch address processing with AI-powered analysis
- **Geocoding-First Enhancement**: Incomplete addresses automatically query Nominatim before AI processing
- **Compare Processing**: Upload and analyze files for address comparison
- **Database Integration**: Connect to SQL Server/Azure SQL for direct data processing
- **Admin Tools**: Job statistics, cleanup, and management endpoints
- **Sample Downloads**: Downloadable template files for testing and development

### Job Persistence
- **SQLite Database**: Persistent job tracking with automatic initialization
- **Database Migration**: Automatic schema updates for existing databases
- **Job History**: Track all processing jobs with status, component, and expiration
- **Automatic Cleanup**: Scheduled cleanup of expired jobs (7-day retention)
- **Webhook Support**: Optional webhook notifications for job completion

### CLI Tools
- **CSV Processing**: Advanced command-line tools for processing address files
- **Batch Operations**: Process multiple files with batch processing modes
- **Address Comparison**: Compare addresses and analyze differences
- **Direct Input Processing**: Process individual addresses from command line

### Database Features
- **SQL Server/Azure SQL Support**: Direct database connectivity and processing
- **Table and Query Modes**: Flexible data extraction from existing databases
- **Preview and Download**: Paginated results with processed file downloads
- **Safe Processing**: Limited record processing for testing and validation

## API v1 Endpoints

### File Processing
- `POST /api/v1/files/upload` — Upload Excel/CSV files for synchronous address processing
- `POST /api/v1/files/upload-async` — Upload files for asynchronous background processing
  - **Body**: `file` (multipart), optional `webhook_url` (string), optional `component` (string: 'upload' or 'compare')
  - **Response**: `{"processing_id": "abc123", "status": "processing", "job_id": 1}`
- `GET /api/v1/files/status/<processing_id>` — Check async job processing status
  - **Response**: Job details with status (processing/completed/failed), progress, output_file, created_at, expires_at
- `GET /api/v1/files/jobs` — Retrieve job history with optional filtering
  - **Query Params**: `status` (all/completed/processing/failed), `component` (upload/compare)
  - **Response**: Array of job objects with full details
- `GET /api/v1/files/download/<filename>` — Download processed files with validation
  - **Returns**: File download if available
  - **410 Gone**: File has expired (past 7-day retention)
  - **404 Not Found**: File does not exist on server
  - **Validation**: Checks job expiration before allowing download

### Address Standardization
- `POST /api/v1/addresses/standardize` — Standardize a single address
- `POST /api/v1/addresses/batch-standardize` — Process multiple addresses in batch

### Comparison Processing
- `POST /api/v1/compare/upload` — Upload files for address comparison analysis

### Database Integration
- `POST /api/v1/database/connect` — Connect to database and get query results directly
  - **Table Mode**: Specify `connectionString`, `sourceType: "table"`, `tableName`, `columnNames[]`, optional `uniqueId`
  - **Query Mode**: Specify `connectionString`, `sourceType: "query"`, `query`
  - **Response**: Returns actual query results with data array, row count, columns, and success status

### Admin Endpoints
- `GET /api/v1/admin/stats` — View job statistics and metrics
  - **Response**: Total jobs, status breakdown, component breakdown, average processing time
- `POST /api/v1/admin/cleanup` — Manually trigger cleanup of expired jobs
  - **Response**: Count of deleted jobs

### Sample Files
- `GET /api/v1/samples/file-upload` — Download sample upload file template
- `GET /api/v1/samples/compare-upload` — Download sample comparison file template

### Legacy Endpoints (still supported)
- `POST /api/db/connect` — Database connection endpoint (legacy)
- `GET /api/processing-status/<id>` — Processing status (legacy)
- `GET /api/preview/<filename>` — File preview (legacy)
- `GET /api/download/<filename>` — File download (legacy)

## Address Processing Enhancement

### Geocoding-First Approach for Incomplete Addresses

The system now intelligently handles incomplete addresses by querying geocoding databases first:

**How It Works:**
1. **Smart Detection**: Checks if address contains state abbreviations, ZIP codes, or commas
2. **Incomplete Address Identified**: Address lacks these components (e.g., "3506 94TH ST")
3. **Geocoding Query**: Queries OpenStreetMap Nominatim API for complete address data
4. **AI Standardization**: Uses enriched geocoded result with Azure OpenAI for final formatting
5. **Complete Result**: Returns full address with city, state, ZIP (like Google Maps)

**Benefits:**
- Handles partial addresses that only contain street information
- Provides Google Maps-like address enrichment
- Backward compatible - complete addresses skip geocoding
- Uses free OpenStreetMap Nominatim API (1-second rate limiting)
- Tracks source with 'geocoding_then_azure_openai' tag

**Example:**
```
Input:  "3506 94TH ST"
Output: "3506 94th Street, Lubbock, TX 79423, USA"
```

## CLI Usage Guide

The AddressIQ backend includes powerful command-line tools for processing addresses directly from the terminal.

### Quick Start

#### 1) Process a CSV file
```bash
python csv_address_processor.py site_addresses_sample.csv
```

#### 2) Process a single address
```bash
# Auto-detect country
python csv_address_processor.py --address "795 sec 22 Pkt-B GGN Haryna"

# Force specific country
python csv_address_processor.py --address "123 High St, London" --country "UK"

# Different output formats
python csv_address_processor.py --address "123 Main St" --format formatted
python csv_address_processor.py --address "123 Main St" --format detailed
python csv_address_processor.py --address "123 Main St" --format json
```

#### 3) Process multiple addresses
```bash
python csv_address_processor.py --address "123 Main St, NYC" "456 Oak Ave, LA" "789 Park Blvd, SF"
```

#### 4) Save results to file
```bash
# Single address → JSON
python csv_address_processor.py --address "123 Main St" --output result.json

# CSV file → processed CSV
python csv_address_processor.py input.csv --output processed_addresses.csv
```

### Advanced CLI Features

#### Batch Processing
```bash
# Process all files in inbound directory
python csv_address_processor.py --batch-process

# Set custom base directory
python csv_address_processor.py --batch-process --base-dir "C:\\AddressIQ\\chatbot-app\\backend"

# Batch comparison processing
python csv_address_processor.py --batch-compare
```

#### Address Comparison
```bash
# Compare two addresses directly
python csv_address_processor.py --compare "123 Main St, New York" "123 Main Street, NYC"

# Compare addresses from CSV file
python csv_address_processor.py comparison.csv --compare-csv
```

#### Advanced Options
```bash
# Specify column name for processing
python csv_address_processor.py input.csv --column "address_field"

# Set batch size for processing
python csv_address_processor.py input.csv --batch-size 10

# Disable free API fallbacks
python csv_address_processor.py input.csv --no-free-apis

# Test API connectivity
python csv_address_processor.py --test-apis

# Generate database statistics
python csv_address_processor.py --db-stats
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Azure OpenAI API access (optional - free APIs available as fallback)
- SQL Server/Azure SQL Database (optional - for database features)

### Installation

1. **Navigate to backend directory**
   ```bash
   cd chatbot-app/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file with your credentials
   CLIENT_ID=your_client_id_here
   CLIENT_SECRET=your_client_secret_here
   WSO2_AUTH_URL=https://api-test.cbre.com:443/token
   AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

### Directory Structure
```
backend/
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (create this)
├── app/                       # Main application package
│   ├── main.py               # Flask routes and API endpoints
│   ├── config/               # Configuration files
│   ├── models/               # Data models
│   └── services/             # Business logic services
├── database/                 # SQLite job database
│   ├── job_manager.py       # Job persistence and management module
│   └── jobs.db              # SQLite database (auto-created on first run)
├── inbound/                  # File upload directory
├── outbound/                 # Processed file output
├── archive/                  # Archived processed files
├── samples/                  # Sample files for API testing
└── __pycache__/             # Python cache files
```

## Job Database

### SQLite Persistence Layer
The application uses SQLite for persistent job tracking:

```python
# Database location
database/jobs.db  # Auto-created on first run

# Schema
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processing_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    component TEXT DEFAULT 'upload',
    input_file TEXT NOT NULL,
    output_file TEXT,
    webhook_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    expires_at TIMESTAMP
)
```

### Job Manager Module
The `database/job_manager.py` module provides:

**Core Functions:**
- `create_job(processing_id, input_file, component='upload', webhook_url=None)` - Create new job
- `update_job_status(processing_id, status, output_file=None, error_message=None)` - Update job
- `get_job(processing_id)` - Retrieve single job by ID
- `get_jobs(status=None, component=None)` - List jobs with optional filtering
- `cleanup_expired_jobs()` - Remove jobs past retention period
- `get_job_stats()` - Get statistics on job counts and processing times

**Features:**
- Automatic database initialization on first run
- Schema migration for existing databases (adds `component` column)
- 7-day retention policy (configurable via `JOB_RETENTION_DAYS` env var)
- Thread-safe operations for async processing
- Webhook support for job completion notifications

### Job Lifecycle
1. **Creation**: Job created with `processing` status when file uploaded
2. **Processing**: Background thread processes file
3. **Completion**: Status updated to `completed` or `failed`
4. **Expiration**: Jobs expire 7 days after creation
5. **Cleanup**: Automatic cleanup removes expired jobs

## Database Integration (SQL Server/Azure SQL)

### Connection String Format
```
Server=your_server;Database=your_database;Trusted_Connection=yes;
# OR for Azure SQL:
Server=tcp:yourserver.database.windows.net,1433;Database=yourdatabase;User ID=username;Password=password;
```

### Table Mode
- Specify table name and column names containing address data
- Optional unique ID column for tracking records
- Safe processing with configurable record limits

### Query Mode
- Write custom SQL queries to extract address data
- Support for complex joins and filtering
- Results processed through standardization pipeline

## API Response Formats

### Standard Success Response
```json
{
  "success": true,
  "data": {
    "processing_id": "uuid-string",
    "status": "queued|processing|completed|failed",
    "message": "Operation completed successfully"
  }
}
```

### Address Standardization Response
```json
{
  "success": true,
  "input_address": "123 Main St, NYC",
  "standardized_address": {
    "street_number": "123",
    "street_name": "Main Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "confidence_score": 0.95
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Configuration

### Environment Variables
Create a `.env` file with the following settings:
```bash
# Azure OpenAI Configuration
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
WSO2_AUTH_URL=https://api-test.cbre.com:443/token
AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id

# Job Retention Configuration
JOB_RETENTION_DAYS=7  # Number of days to retain completed jobs
```

### Job Manager Configuration
The `database/job_manager.py` module provides:
- **Automatic Database Initialization**: Creates `jobs.db` on first run
- **Schema Migration**: Automatically updates existing databases with new columns
- **Job CRUD Operations**: Create, read, update, delete operations for job tracking
- **Cleanup Scheduling**: Automatic cleanup of expired jobs based on retention policy

### Address Processing Configuration
The system uses configurable prompts and settings in `app/config/address_config.py`:

- **System Prompts**: Customizable AI prompts for different processing scenarios
- **Output Formats**: Control standardized address output structure
- **Processing Options**: Batch sizes, timeout settings, retry logic
- **API Settings**: Azure OpenAI configuration and fallback options

### File Processing Options
- **Supported Formats**: Excel (.xlsx, .xls), CSV (.csv)
- **Maximum File Size**: 50MB default (configurable)
- **Processing Limits**: Configurable batch sizes and record limits
- **Output Locations**: Automatic file organization in inbound/outbound/archive
- **Async Processing**: Background processing with threading for non-blocking operations

## Error Handling

The backend includes comprehensive error handling for:
- **File Processing Errors**: Invalid file formats, corrupted files, size limits
- **API Connectivity Issues**: Azure OpenAI service availability, authentication
- **Database Connection Problems**: Invalid connection strings, network issues
- **Address Processing Failures**: Unparseable addresses, service timeouts

## Development

### Running in Development Mode
```bash
# Enable debug mode
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows

# Run with auto-reload
python run.py
```

### Testing
```bash
# Test API connectivity
python csv_address_processor.py --test-apis

# Process sample data
python csv_address_processor.py site_addresses_sample.csv

# Test database connection
python database_workflow_demo.py
```

### Adding New Features
1. **API Endpoints**: Add new routes in `app/main.py`
2. **Business Logic**: Implement services in `app/services/`
3. **Configuration**: Update settings in `app/config/`
4. **Models**: Add data structures in `app/models/`

## Troubleshooting

### Common Issues

**1. Authentication Errors**
- Verify Azure OpenAI credentials in `.env` file
- Check WSO2 gateway connectivity
- Validate API key format and permissions

**2. File Processing Issues**
- Ensure files are in supported formats (Excel/CSV)
- Check file size limits (50MB default)
- Verify column names and data structure

**3. Database Connection Problems**
- Validate connection string format
- Test network connectivity to database server
- Check user permissions for database access

**4. Address Processing Failures**
- Review address format and completeness
- Check Azure OpenAI service availability
- Verify prompt configuration settings

### Logging
The application logs detailed information for debugging:
- **API Requests**: All incoming requests and responses
- **Processing Steps**: Step-by-step address processing logs
- **Error Details**: Comprehensive error messages and stack traces
- **Performance Metrics**: Processing times and resource usage

## License

[Add your license information here]

## Support

For technical support and questions:
- **API Documentation**: Use the Public API interface in the frontend
- **CLI Help**: Run `python csv_address_processor.py --help`
- **Configuration Guide**: Check `app/config/address_config.py`
- **Sample Data**: Use files in the `samples/` directory for testing

---

**AddressIQ Backend** - Powerful address intelligence processing engine with comprehensive API and CLI capabilities.

# Multiple addresses → JSON
python csv_address_processor.py --address "123 Main St" "456 Oak Ave" --output results.json
```

### 5) Batch modes (inbound/outbound/archive folders)
```bash
# Process all CSV files in inbound/
python csv_address_processor.py --batch-process

# Process all comparison CSV files in inbound/
python csv_address_processor.py --batch-compare

# Use a custom base directory (defaults to current folder)
python csv_address_processor.py --batch-process --base-dir "C:\\AddressIQ\\chatbot-app\\backend"
```

### 6) Compare addresses
```bash
# Compare two free-text addresses
python csv_address_processor.py --compare "123 Main St, NYC" "123 Main Street, New York"

# Compare pairs from a CSV file
python csv_address_processor.py comparison_data.csv --compare-csv
```

### 7) Utilities
```bash
# Database stats
python csv_address_processor.py --db-stats

# Test connectivity to free APIs
python csv_address_processor.py --test-apis
```

## ⚙️ Options overview

- Input selection (mutually exclusive):
  - Positional CSV file: `input_file`
  - `--address` one or more values
  - `--batch-process` process all inbound files
  - `--batch-compare` process all inbound comparison files
- CSV options: `-o/--output`, `-c/--column`, `-b/--batch-size` (default 5)
- Address options: `--country`, `-f/--format` (`json`|`formatted`|`detailed`), `--output`
- Comparison: `--compare ADDRESS1 ADDRESS2`, `--compare-csv`
- Directory: `--base-dir` to set root for `inbound/`, `outbound/`, `archive/`
- Performance: `--no-free-apis` to disable free API enhancement
- Utilities: `--db-stats`, `--test-apis`

## 📋 Output formats

### `--format formatted` (clean & simple)
```
Original: 795 sec 22 Pkt-B GGN Haryna
Formatted: 795 Sector 22, Pocket B, Gurgaon, Haryana, India
Confidence: medium
From cache: false
Status: success
```

### `--format json` (default – full response)
```json
{
  "street_number": "795",
  "street_name": "Sector 22",
  "unit_type": "Pocket",
  "unit_number": "B",
  "city": "Gurgaon",
  "state": "Haryana",
  "country": "India",
  "formatted_address": "795 Sector 22, Pocket B, Gurgaon, Haryana, India",
  "confidence": "medium"
}
```

### `--format detailed` (complete data)
Includes all fields plus API source, processing time, database info, etc.

## 🌍 Country auto-detection

The system detects countries from address patterns and only needs `--country` for ambiguous inputs or to force formatting.

## ⚡ Performance features

- Batch processing for fewer API calls (default batch size 5)
- Database caching to reuse processed addresses
- Smart fallbacks to individual processing when needed

## � Directories

- `inbound/` drop your input files here for batch modes
- `outbound/` processed results are written here
- `archive/` processed inputs are archived here
- Configure root with `--base-dir` (defaults to current working directory)

## 🔄 Backward compatibility

Existing CSV processing continues to work:
```bash
python csv_address_processor.py site_addresses_sample.csv
```

All new features are additive to existing workflows.
