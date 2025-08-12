# AddressIQ PowerShell Launcher
# Usage: .\addressiq.ps1 --address "123 Main St, NYC, NY"

$pythonPath = "C:\Users\DGaur\AppData\Local\anaconda3\python.exe"
$scriptPath = Join-Path $PSScriptRoot "csv_address_processor.py"

# Check if Python exists
if (-not (Test-Path $pythonPath)) {
    Write-Host "❌ Python not found at: $pythonPath" -ForegroundColor Red
    Write-Host "Please update the path in addressiq.ps1" -ForegroundColor Yellow
    exit 1
}

# Run the script with all arguments
& $pythonPath $scriptPath $args
