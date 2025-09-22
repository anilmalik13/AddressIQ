# AddressIQ Backend

A powerful Python Flask backend providing comprehensive address intelligence services through RESTful APIs, CLI tools, and database integration capabilities.

## Overview

The AddressIQ backend serves as the core processing engine for address standardization, file processing, and data management. It combines Azure OpenAI integration, database connectivity, and flexible CLI tools to deliver enterprise-grade address intelligence solutions.

## Features

### API Endpoints (v1)
- **File Processing**: Upload and process Excel/CSV files for batch address standardization
- **Address Standardization**: Single and batch address processing with AI-powered analysis
- **Compare Processing**: Upload and analyze files for address comparison
- **Database Integration**: Connect to SQL Server/Azure SQL for direct data processing
- **Sample Downloads**: Downloadable template files for testing and development

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
- `POST /api/v1/files/upload` — Upload Excel/CSV files for address processing
- `GET /api/v1/files/status/<processing_id>` — Check file processing status
- `GET /api/v1/files/download/<filename>` — Download processed files

### Address Standardization
- `POST /api/v1/addresses/standardize` — Standardize a single address
- `POST /api/v1/addresses/batch-standardize` — Process multiple addresses in batch

### Comparison Processing
- `POST /api/v1/compare/upload` — Upload files for address comparison analysis

### Database Integration
- `POST /api/v1/database/connect` — Connect to database and process address data

### Sample Files
- `GET /api/v1/samples/file-upload` — Download sample upload file template
- `GET /api/v1/samples/compare-upload` — Download sample comparison file template

### Legacy Endpoints (still supported)
- `POST /api/db/connect` — Database connection endpoint (legacy)
- `GET /api/processing-status/<id>` — Processing status (legacy)
- `GET /api/preview/<filename>` — File preview (legacy)
- `GET /api/download/<filename>` — File download (legacy)

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
├── inbound/                  # File upload directory
├── outbound/                 # Processed file output
├── archive/                  # Archived processed files
├── samples/                  # Sample files for API testing
└── __pycache__/             # Python cache files
```

## Database Integration

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
