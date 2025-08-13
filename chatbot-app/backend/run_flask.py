#!/usr/bin/env python3
"""
Run script for the AddressIQ Flask application
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
