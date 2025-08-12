@echo off
REM AddressIQ - Easy command launcher
REM Usage: addressiq --address "123 Main St, NYC, NY"

cd /d "%~dp0"
"C:\Users\DGaur\AppData\Local\anaconda3\python.exe" csv_address_processor.py %*
