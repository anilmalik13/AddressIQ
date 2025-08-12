# AddressIQ Enhanced Directory Management

## Overview
The AddressIQ system now features advanced directory management with automatic file processing workflows. This enhancement follows industry best practices for batch processing systems.

## Directory Structure

```
backend/
├── inbound/          # Place CSV files here for processing
├── outbound/         # Processed files are saved here
├── archive/          # Original files are moved here after processing
└── csv_address_processor.py
```

## Workflow

### 1. **Inbound Directory** 📥
- Place your CSV files here for automatic processing
- Supports both `.csv` and `.xlsx` files
- Files are automatically detected and processed

### 2. **Processing** 🔄
- System automatically cleans outbound directory before processing
- Processes all files in inbound directory
- Uses efficient batch processing with database caching
- Adds timestamped filenames to avoid conflicts

### 3. **Outbound Directory** 📤
- Cleaned before each batch processing run
- Contains processed files with standardized addresses
- Files include timestamp in name: `filename_processed_YYYYMMDD_HHMMSS.csv`

### 4. **Archive Directory** 📦
- Original files are moved here after successful processing
- Files include timestamp: `filename_YYYYMMDD_HHMMSS.csv`
- Provides backup and audit trail

## Usage Examples

### Batch Processing (Recommended)
```bash
# Process all files in inbound directory
python csv_address_processor.py --batch-process

# With custom batch size
python csv_address_processor.py --batch-process -b 10

# With custom base directory
python csv_address_processor.py --batch-process --base-dir "/path/to/data"
```

### Traditional Single File Processing
```bash
# Process a specific file (saves to outbound directory)
python csv_address_processor.py addresses.csv

# With custom output location
python csv_address_processor.py addresses.csv -o custom_output.csv
```

### Direct Address Processing (No files)
```bash
# Single address
python csv_address_processor.py --address "123 Main St, NYC, NY"

# Multiple addresses
python csv_address_processor.py --addresses "123 Main St, NYC" "456 Oak Ave, LA"
```

## Benefits

### 🎯 **Organized Workflow**
- Clear separation of input, output, and archive files
- No more cluttered directories with mixed files
- Professional batch processing setup

### 🔄 **Automatic File Management**
- Inbound files automatically processed and archived
- Outbound directory cleaned before each run
- Timestamped files prevent overwrites

### 📊 **Audit Trail**
- All original files preserved in archive
- Processing timestamps for tracking
- Complete history of all processing runs

### 🚀 **Efficiency**
- Batch processing of multiple files
- Database caching reduces API calls
- Parallel processing when possible

## Directory Management Commands

### Setup Directories Only
```bash
# Initialize directory structure
python csv_address_processor.py --batch-process
# (Will create directories and show status, then exit if no files found)
```

### Check Status
```bash
# View database statistics
python csv_address_processor.py --db-stats

# Test API connections
python csv_address_processor.py --test-apis
```

## Advanced Configuration

### Custom Base Directory
```bash
# Use different base directory
python csv_address_processor.py --batch-process --base-dir "/data/address_processing"
```

This will create:
- `/data/address_processing/inbound/`
- `/data/address_processing/outbound/`
- `/data/address_processing/archive/`

### Integration with Other Systems

The directory structure makes it easy to integrate with:
- **File watching services** (monitor inbound directory)
- **Scheduled tasks** (run batch processing periodically)
- **CI/CD pipelines** (automated data processing)
- **FTP/SFTP uploads** (direct upload to inbound directory)

## File Processing Results

### Example Output Structure
```
outbound/
├── customers_processed_20250812_143022.csv
├── properties_processed_20250812_143045.csv
└── vendors_processed_20250812_143108.csv

archive/
├── customers_20250812_143022.csv
├── properties_20250812_143045.csv
└── vendors_20250812_143108.csv
```

### Processing Summary
Each batch run provides:
- ✅ Files processed successfully
- ❌ Files with errors  
- 📊 Database cache statistics
- 🕒 Processing timestamps
- 📍 File locations

## Best Practices

1. **Regular Monitoring**: Check inbound directory regularly for new files
2. **Archive Management**: Periodically clean old files from archive directory
3. **Error Handling**: Review any files that fail processing
4. **Database Maintenance**: Monitor cache hit rates for performance
5. **Backup Strategy**: Include archive directory in backup procedures

## Migration from Old System

To migrate from the old system:

1. **Move existing CSV files** to `inbound/` directory
2. **Run batch processing**: `python csv_address_processor.py --batch-process`
3. **Verify results** in `outbound/` directory
4. **Update any scripts** to use new directory structure

The system maintains full backward compatibility - you can still process individual files directly if needed.
