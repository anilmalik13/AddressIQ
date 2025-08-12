#!/usr/bin/env python3
"""
AddressIQ Smart Launcher - Automatically finds Python and runs the processor
Usage: python addressiq.py --address "123 Main St, NYC, NY"
"""
import sys
import subprocess
import os
from pathlib import Path

def find_python():
    """Find the correct Python executable"""
    # Try the specific Anaconda path first
    anaconda_python = Path("C:/Users/DGaur/AppData/Local/anaconda3/python.exe")
    if anaconda_python.exists():
        return str(anaconda_python)
    
    # Try other common paths
    paths_to_try = [
        "python",
        "python3", 
        "py",
        Path.home() / "anaconda3" / "python.exe",
        Path.home() / "miniconda3" / "python.exe",
        Path("C:/Python39/python.exe"),
        Path("C:/Python310/python.exe"),
        Path("C:/Python311/python.exe"),
        Path("C:/Python312/python.exe")
    ]
    
    for path in paths_to_try:
        try:
            result = subprocess.run([str(path), "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Found Python: {path}")
                return str(path)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    
    return None

def main():
    print("🚀 AddressIQ Smart Launcher")
    print("=" * 40)
    
    python_exe = find_python()
    if not python_exe:
        print("❌ Could not find Python installation!")
        print("\nTried these locations:")
        print("  - C:/Users/DGaur/AppData/Local/anaconda3/python.exe")
        print("  - System PATH (python, python3, py)")
        print("  - Common installation directories")
        print("\nPlease ensure Python is installed and accessible.")
        sys.exit(1)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    main_script = script_dir / "csv_address_processor.py"
    
    if not main_script.exists():
        print(f"❌ Main script not found: {main_script}")
        sys.exit(1)
    
    # Run the main script with all arguments
    print(f"🐍 Using Python: {python_exe}")
    print(f"📄 Running: {main_script.name}")
    print()
    
    cmd = [python_exe, str(main_script)] + sys.argv[1:]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
