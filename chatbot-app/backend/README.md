# AddressIQ - Usage Guide

## Quick Start

The AddressIQ CSV processor supports both CSV files and direct address input!

## 🎯 Usage Examples

### 1. Process CSV File (Original functionality)
```bash
python csv_address_processor.py site_addresses_sample.csv
```

### 2. Process Single Address
```bash
# Basic usage (auto-detects country)
python csv_address_processor.py --address "795 sec 22 Pkt-B GGN Haryna"

# With country specification
python csv_address_processor.py --address "123 High St, London" --country "UK"

# Different output formats
python csv_address_processor.py --address "123 Main St" --format formatted
python csv_address_processor.py --address "123 Main St" --format detailed
```

### 3. Process Multiple Addresses
```bash
python csv_address_processor.py --addresses "123 Main St, NYC" "456 Oak Ave, LA" "789 Park Blvd, SF"
```

### 4. Save Results to File
```bash
# Single address to JSON file
python csv_address_processor.py --address "123 Main St" --output result.json

# Multiple addresses to JSON file
python csv_address_processor.py --addresses "123 Main St" "456 Oak Ave" --output results.json
```

### 5. Database Statistics
```bash
python csv_address_processor.py --db-stats
```

## 📋 Output Formats

### `--format formatted` (Clean & Simple)
```
Original: 795 sec 22 Pkt-B GGN Haryna
Formatted: 795 Sector 22, Pocket B, Gurgaon, Haryana, India
Confidence: medium
From cache: false
Status: success
```

### `--format json` (Default - Full Response)
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

### `--format detailed` (Complete Data)
Includes all fields plus API source, processing time, database info, etc.

## 🌍 Country Auto-Detection

The system automatically detects countries from address patterns:

- **Indian addresses**: "GGN" → Gurgaon, "sec 22" → Sector 22
- **US addresses**: "NYC, NY" → New York, New York
- **UK addresses**: "London SW1A 1AA" → London, UK
- **And 195+ more countries**

You only need `--country` for ambiguous addresses or to force specific formatting.

## ⚡ Performance Features

- **Batch Processing**: Processes multiple addresses in single API calls (60% faster)
- **Database Caching**: Reuses previously processed addresses
- **Smart Fallbacks**: Falls back to individual processing if batch fails

## 🔧 Advanced Options

```bash
# CSV processing with custom batch size
python csv_address_processor.py addresses.csv -b 10

# Specify output file for CSV
python csv_address_processor.py addresses.csv -o custom_output.csv

# Process specific column in CSV
python csv_address_processor.py addresses.csv -c "Street Address"

# Test API connectivity
python csv_address_processor.py --test-apis
```

## 🚀 Real-World Examples

```bash
# Indian address
python csv_address_processor.py --address "Plot 123, Sector 45, Noida, UP"

# US address
python csv_address_processor.py --address "1600 Pennsylvania Ave, Washington, DC"

# UK address  
python csv_address_processor.py --address "10 Downing Street, London"

# Mixed international batch
python csv_address_processor.py --addresses \
  "795 sec 22 Pkt-B GGN Haryna" \
  "123 Main St, NYC, NY" \
  "10 Downing Street, London"
```

## 📊 Database Benefits

- **Cache Hit Rate**: See how many addresses are reused (saves API calls)
- **Performance Tracking**: Monitor processing efficiency
- **Cost Savings**: Avoid reprocessing the same addresses

## 🔄 Backward Compatibility

All existing CSV processing functionality remains unchanged:
```bash
# This still works exactly the same
python csv_address_processor.py site_addresses_sample.csv
```

The new features are additive - your existing workflows continue to work!
