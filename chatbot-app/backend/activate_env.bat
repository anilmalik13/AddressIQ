@echo off
echo 🚀 Activating AddressIQ Virtual Environment...
set "PATH=C:\Users\DGaur\AppData\Local\anaconda3\envs\AddressIQ_Env\Scripts;%PATH%"
set "CONDA_DEFAULT_ENV=AddressIQ_Env"
set "VIRTUAL_ENV=C:\Users\DGaur\AppData\Local\anaconda3\envs\AddressIQ_Env"
prompt (AddressIQ_Env) $P$G
echo ✅ Virtual environment activated!
echo.
echo 📋 Quick commands:
echo    python csv_address_processor.py --address "123 Main St"
echo    python csv_address_processor.py myfile.csv  
echo    python csv_address_processor.py --test-apis
echo    python csv_address_processor.py --db-stats
echo.
cmd /k
