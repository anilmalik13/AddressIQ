# AddressIQ Backend – CLI Usage Guide

## Web API additions (Database Connect)

Endpoints used by the Database Connect UI:

- `POST /api/db/connect` — Start a DB fetch + process job. Payload: `{ mode: 'format', connectionString, sourceType: 'table'|'query', tableName?, uniqueId?, columnNames?, query?, limit? }`.
- `GET /api/processing-status/<id>` — Poll current status and progress; includes recent logs and output_file on completion.
- `GET /api/processing-status/<id>/logs` — Retrieve recent log entries only.
- `GET /api/preview/<filename>` — Paginated preview of processed outbound file (CSV/Excel). Query: `page`, `page_size`.
- `GET /api/download/<filename>` — Download processed CSV from `outbound/`.

Notes:
- Only outbound (processed) files are downloadable.
- Preview returns `{ columns: string[], rows: any[] }`.
- The job uses a safe default record limit (10) unless overridden.

## Quick start

The AddressIQ processor supports CSV files, batch modes, address comparison, and direct address input.

## 🎯 Common commands

### 1) Process a CSV file
```bash
python csv_address_processor.py site_addresses_sample.csv
```

### 2) Process a single address
```bash
# Auto-detect country
python csv_address_processor.py --address "795 sec 22 Pkt-B GGN Haryna"

# Force country
python csv_address_processor.py --address "123 High St, London" --country "UK"

# Output formats
python csv_address_processor.py --address "123 Main St" --format formatted
python csv_address_processor.py --address "123 Main St" --format detailed
```

### 3) Process multiple addresses
```bash
python csv_address_processor.py --address "123 Main St, NYC" "456 Oak Ave, LA" "789 Park Blvd, SF"
```

### 4) Save results to file
```bash
# Single address → JSON
python csv_address_processor.py --address "123 Main St" --output result.json

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
