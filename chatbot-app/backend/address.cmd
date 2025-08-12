@echo off
REM Simplified launcher for AddressIQ address processing using virtual environment
REM This script activates the virtual environment and runs address processing

REM Activate virtual environment
call .\addressiq_venv\Scripts\activate.bat

REM Run the address processor with all passed arguments
python csv_address_processor.py %*
