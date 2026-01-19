#!/usr/bin/env python3
"""
Quick test script for individual address splitting
"""

from address_splitter import AddressSplitter

def test_individual_addresses():
    """Test a few specific addresses"""
    
    # Initialize both splitters
    rule_splitter = AddressSplitter(use_gpt=False)
    
    test_addresses = [
        ("5250 NW 86th St, 8651, 8751, 8801 Northpark Dr", None),
        ("34 Fairview St and 45 Oakwood Ave", None),
        ("6120 & 6132 Brookshire Blvd, Units M, N & F", None),
        ("211-245 Wheelhouse Lane", None),
        ("2504 and 2506 Zeppelin Rd", "2510 and 2520 Aviation Way"),
    ]
    
    print("=" * 80)
    print("INDIVIDUAL ADDRESS SPLITTING TEST")
    print("=" * 80)
    
    for i, (addr1, addr2) in enumerate(test_addresses, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}:")
        print(f"  Address 1: {addr1}")
        if addr2:
            print(f"  Address 2: {addr2}")
        print(f"{'='*80}")
        
        # Test with rule-based
        result = rule_splitter.analyze_and_split(addr1, addr2)
        
        print(f"\n📋 RULE-BASED RESULT:")
        print(f"  Should Split: {result['should_split']}")
        print(f"  Reason: {result['split_reason']}")
        print(f"  Method: {result['method_used']}")
        
        if result['should_split']:
            print(f"  📍 Split into {result['split_count']} addresses:")
            for j, addr in enumerate(result['addresses'], 1):
                print(f"     {j}. {addr}")
        else:
            print(f"  📍 No split: {result['addresses'][0]}")

if __name__ == "__main__":
    test_individual_addresses()
