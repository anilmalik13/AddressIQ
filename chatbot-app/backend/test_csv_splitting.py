#!/usr/bin/env python3
"""
Test CSV splitting with all rule examples
"""
import csv
from address_splitter import AddressSplitter

splitter = AddressSplitter()

# Read the test CSV
csv_file = 'samples/test_splitting_rules.csv'

print('='*80)
print('CSV ADDRESS SPLITTING TEST')
print('='*80)

passed = 0
failed = 0
total = 0

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        total += 1
        master_id = row['MasterId']
        name = row['Name']
        address1 = row['Address1']
        address2 = row['Address2'] if row['Address2'] != 'NULL' else None
        expected_count = int(row['ExpectedSplitCount'])
        rule = row['SplitRule']
        
        # Test the splitting
        result = splitter.analyze_and_split(address1, address2)
        actual_count = result['split_count']
        
        status = '✅ PASS' if actual_count == expected_count else '❌ FAIL'
        if actual_count == expected_count:
            passed += 1
        else:
            failed += 1
        
        print(f'\n{status} [{master_id}] {name}')
        print(f'  Rule: {rule}')
        print(f'  Address1: {address1}')
        if address2:
            print(f'  Address2: {address2}')
        print(f'  Expected: {expected_count} | Actual: {actual_count}')
        print(f'  Reason: {result["split_reason"]}')
        
        if result['should_split'] and actual_count <= 6:
            for i, addr in enumerate(result['addresses'], 1):
                print(f'    {i}. {addr}')

print('\n' + '='*80)
print(f'SUMMARY: {passed} passed, {failed} failed out of {total} tests')
print('='*80)
