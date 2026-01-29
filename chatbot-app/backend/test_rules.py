#!/usr/bin/env python3
"""
Test all address splitting rules with examples from the requirements
"""
from address_splitter import AddressSplitter

splitter = AddressSplitter()

# Test cases from your rules
test_cases = [
    # NO SPLIT cases
    ('211-245 Wheelhouse Lane', False, 'Range pattern'),
    ('96-100 Pane Road', False, 'Range pattern'),
    ('3800 West Ray Road Unit B3 (B15-B20)', False, 'Fractional identifiers'),
    ('6120 & 6132 Brookshire Blvd, Units M, N & F', False, 'Fractional identifiers'),
    ('140 Vann St NE, 1st Floor - 310/320', False, 'Fractional identifiers'),
    ('E of S Aspen Ave; S/S of E 91st S', False, 'Directional identifiers'),
    ('NEQ OF THE SEQ OF SECTION 26, TOWNSHIP 15 SOUTH, RANGE 67 WEST OF THE 6TH P.M.', False, 'Directional'),
    ('W/L of S. Rangerville Road, SW of S. Expressway 83', False, 'Directional'),
    ('1/4 Mile South of 195th Ave SE on Kandi-Meeker Rd SE', False, 'Directional'),
    ('Highway 40 and K', False, 'No street numbers'),
    ('Main Street (Hwy 20)', False, 'No and/&'),
    
    # SHOULD SPLIT cases
    ('5250 NW 86th St, 8651, 8751, 8801 Northpark Dr', True, 'Comma-separated numbers'),
    ('2905 S Regal St, 2908 E 29th Ave & 2917 S Regal St', True, 'and/& with commas'),
    ('8894 and 8896 Fort Smallwood Rd', True, 'and without special chars'),
    ('34 Fairview St and 45 Oakwood Ave', True, 'and without special chars'),
    ('10659 West Fairview Avenue & 1421 North Five Mile Road', True, '& without special chars'),
    
    # CSV DATA cases
    ('Hwy 180 and Jack Borden Way', True, 'CSV Row 1'),
    ('10255 and 10261 Iron Rock Way', True, 'CSV Row 2'),
    ('0, 19, 20, 97 & 105 Morrisville Plaza', True, 'CSV Row 3'),
    ('14942 and 15012 South Post Oak Road', True, 'CSV Row 4'),
]

print('='*80)
print('ADDRESS SPLITTING TEST RESULTS')
print('='*80)

passed = 0
failed = 0

for addr, should_split, category in test_cases:
    result = splitter.analyze_and_split(addr)
    actual_split = result['should_split']
    
    status = '✅ PASS' if actual_split == should_split else '❌ FAIL'
    if actual_split == should_split:
        passed += 1
    else:
        failed += 1
    
    print(f'\n{status} [{category}]')
    print(f'  Address: {addr[:70]}')
    print(f'  Expected Split: {should_split} | Actual: {actual_split}')
    print(f'  Reason: {result["split_reason"]}')
    if actual_split:
        print(f'  Split Count: {result["split_count"]}')
        if result['split_count'] <= 5:
            for i, a in enumerate(result['addresses'], 1):
                print(f'    {i}. {a}')

print('\n' + '='*80)
print(f'SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests')
print('='*80)
