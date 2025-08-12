# AddressIQ Virtual Environment PowerShell Activation Script
Write-Host "🚀 Activating AddressIQ Virtual Environment..." -ForegroundColor Green

# Set environment variables
$env:PATH = "C:\Users\DGaur\AppData\Local\anaconda3\envs\AddressIQ_Env\Scripts;" + $env:PATH
$env:CONDA_DEFAULT_ENV = "AddressIQ_Env"
$env:VIRTUAL_ENV = "C:\Users\DGaur\AppData\Local\anaconda3\envs\AddressIQ_Env"

# Update prompt
function global:prompt {
    "(AddressIQ_Env) PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

Write-Host "✅ Virtual environment activated!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Quick commands:" -ForegroundColor Cyan
Write-Host "   python csv_address_processor.py --address '123 Main St'" -ForegroundColor Yellow
Write-Host "   python csv_address_processor.py myfile.csv" -ForegroundColor Yellow  
Write-Host "   python csv_address_processor.py --test-apis" -ForegroundColor Yellow
Write-Host "   python csv_address_processor.py --db-stats" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔧 Python Path: $env:VIRTUAL_ENV\python.exe" -ForegroundColor Gray
