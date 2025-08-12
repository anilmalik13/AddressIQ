# AddressIQ Easy Launcher Configuration

## Quick Start

You can now use AddressIQ with these simple commands:

### Option 1: Batch Script (Windows Command Prompt)
```cmd
addressiq --address "123 Main St, NYC, NY"
addressiq --address "123 Main St" "456 Oak Ave" "789 Pine Rd"
addressiq --batch-process
addressiq myfile.csv
```

### Option 2: PowerShell Script
```powershell
.\addressiq.ps1 --address "123 Main St, NYC, NY"
.\addressiq.ps1 --address "123 Main St" "456 Oak Ave" 
.\addressiq.ps1 --batch-process
```

### Option 3: Python Wrapper (Cross-platform)
```bash
python addressiq.py --address "123 Main St, NYC, NY"
python addressiq.py --address "123 Main St" "456 Oak Ave"
python addressiq.py --batch-process
```

## Setup Instructions

### For Batch Script (Easiest)
1. Open Command Prompt as Administrator
2. Navigate to your AddressIQ backend folder:
   ```cmd
   cd "C:\Users\DGaur\AddressIQ_Env\AddressIQ\chatbot-app\backend"
   ```
3. Add current directory to PATH (temporary):
   ```cmd
   set PATH=%PATH%;C:\Users\DGaur\AddressIQ_Env\AddressIQ\chatbot-app\backend
   ```
4. Now use anywhere: `addressiq --address "123 Main St"`

### For Permanent PATH (Recommended)
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", find "Path" and click "Edit"
4. Click "New" and add: `C:\Users\DGaur\AddressIQ_Env\AddressIQ\chatbot-app\backend`
5. Click "OK" to save
6. Open new Command Prompt and use: `addressiq --address "123 Main St"`

### For PowerShell Profile (Advanced)
1. Open PowerShell
2. Run: `notepad $PROFILE` (create if doesn't exist)
3. Add this line:
   ```powershell
   function addressiq { & "C:\Users\DGaur\AddressIQ_Env\AddressIQ\chatbot-app\backend\addressiq.ps1" $args }
   ```
4. Save and restart PowerShell
5. Use: `addressiq --address "123 Main St"`

## Examples

```bash
# Single address
addressiq -a "123 Main Street, New York, NY 10001"

# Multiple addresses
addressiq -a "123 Main St" "456 Oak Ave" "789 Pine Road"

# With country specification
addressiq -a "123 High Street, London" --country UK

# Different output formats
addressiq -a "123 Main St" --format formatted

# Process CSV file
addressiq myfile.csv

# Process all files in inbound directory
addressiq --batch-process

# Test free APIs
addressiq --test-apis

# Show database statistics
addressiq --db-stats
```

## Files Created

- `addressiq.bat` - Windows batch script
- `addressiq.ps1` - PowerShell script  
- `addressiq.py` - Python wrapper with auto-detection
- `LAUNCHER_README.md` - This file

## Troubleshooting

If Python path is different, edit the scripts:
- In `addressiq.bat`: Change the Python path on line 5
- In `addressiq.ps1`: Change `$pythonPath` on line 4
- `addressiq.py` will try to auto-detect Python location

## Current Python Path
The scripts are configured for: `C:\Users\DGaur\AppData\Local\anaconda3\python.exe`
