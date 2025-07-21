#!/usr/bin/env python3
"""
Example script demonstrating address standardization using Azure OpenAI
"""

from app.services.azure_openai import standardize_address, standardize_multiple_addresses
import json

def main():
    # Example raw addresses that need standardization
    sample_addresses = [
        "123 main st apt 4b new york ny 10001",
        "456 oak ave suite 200, los angeles, california 90210",
        "789 elm drive, unit 5A, chicago il 60601",
        "PO Box 123, Miami FL 33101",
        "1000 broadway, 15th floor, NYC, NY 10001"
    ]
    
    print("=== Address Standardization Example ===\n")
    
    # Example 1: Single address standardization
    print("1. Single Address Standardization:")
    print("-" * 40)
    raw_address = sample_addresses[0]
    print(f"Raw Address: {raw_address}")
    
    result = standardize_address(raw_address)
    print(f"Standardized Result:")
    print(json.dumps(result, indent=2))
    print("\n")
    
    # Example 2: Multiple addresses
    print("2. Multiple Address Standardization:")
    print("-" * 40)
    
    results = standardize_multiple_addresses(sample_addresses)
    
    for i, (raw, standardized) in enumerate(zip(sample_addresses, results)):
        print(f"Address {i+1}:")
        print(f"  Raw: {raw}")
        if 'error' not in standardized:
            print(f"  Standardized: {standardized.get('formatted_address', 'N/A')}")
            print(f"  Confidence: {standardized.get('confidence', 'N/A')}")
            if standardized.get('issues'):
                print(f"  Issues: {', '.join(standardized['issues'])}")
        else:
            print(f"  Error: {standardized['error']}")
        print()

if __name__ == "__main__":
    main()
