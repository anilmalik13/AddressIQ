#!/usr/bin/env python3
"""
Test script for file upload functionality
This script tests the new file upload API endpoint
"""

import requests
import os
import pandas as pd
from datetime import datetime

def create_test_csv():
    """Create a test CSV file with sample addresses"""
    test_data = {
        'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'address': [
            '123 Main St, New York, NY 10001',
            '456 Oak Ave, Los Angeles, CA 90210',
            '789 Pine Rd, Chicago, IL 60601'
        ],
        'phone': ['555-1234', '555-5678', '555-9012']
    }
    
    df = pd.DataFrame(test_data)
    test_file = 'test_addresses.csv'
    df.to_csv(test_file, index=False)
    return test_file

def test_file_upload(file_path):
    """Test the file upload endpoint"""
    url = 'http://localhost:5001/api/upload-excel'
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing upload: {e}")
        return False

def test_address_processing():
    """Test the address processing endpoint"""
    url = 'http://localhost:5001/api/process-address'
    test_address = "123 Main Street, New York, NY 10001"
    
    try:
        data = {'address': test_address}
        response = requests.post(url, json=data)
        
        print(f"Address Processing Status: {response.status_code}")
        print(f"Address Processing Response: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing address processing: {e}")
        return False

def test_list_files():
    """Test the list uploaded files endpoint"""
    url = 'http://localhost:5001/api/uploaded-files'
    
    try:
        response = requests.get(url)
        
        print(f"List Files Status: {response.status_code}")
        print(f"List Files Response: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing file listing: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing File Upload API")
    print("=" * 50)
    
    # Create test file
    print("1. Creating test CSV file...")
    test_file = create_test_csv()
    print(f"Created: {test_file}")
    
    # Test file upload
    print("\n2. Testing file upload...")
    if test_file_upload(test_file):
        print("✅ File upload test passed!")
    else:
        print("❌ File upload test failed!")
    
    # Test address processing
    print("\n3. Testing address processing...")
    if test_address_processing():
        print("✅ Address processing test passed!")
    else:
        print("❌ Address processing test failed!")
    
    # Test file listing
    print("\n4. Testing file listing...")
    if test_list_files():
        print("✅ File listing test passed!")
    else:
        print("❌ File listing test failed!")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🧹 Cleaned up test file: {test_file}")
    
    print("\n🎉 All tests completed!")
