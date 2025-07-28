#!/usr/bin/env python3
"""
Quick debug script to test geocoding APIs
"""

import requests
import time
import json

def test_nominatim_simple():
    """Test Nominatim with a simple address"""
    test_address = "2 Harbour Exchange Square, London, E14 9GE"
    
    params = {
        'q': test_address,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }
    
    headers = {
        'User-Agent': 'AddressIQ-Processor/1.0 (contact@addressiq.com)'
    }
    
    print(f"Testing Nominatim with: {test_address}")
    
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            if data and len(data) > 0:
                result = data[0]
                lat = result.get('lat', '')
                lon = result.get('lon', '')
                print(f"Coordinates: {lat}, {lon}")
                return True
        else:
            print(f"Error response: {response.text}")
        
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_nominatim_simple()
