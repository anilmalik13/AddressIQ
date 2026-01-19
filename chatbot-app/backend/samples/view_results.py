import pandas as pd

# Read the standardized output
df = pd.read_csv('output_real_standardized.csv')

print("=" * 130)
print("STANDARDIZED ADDRESS RESULTS WITH SPLITTING")
print("=" * 130)
print(f"\nTotal addresses processed: {len(df)} (from 5 original rows)")
print()

for idx, row in df.iterrows():
    # Build street address
    num = row['Combined_Address_standardized_street_number']
    name = row['Combined_Address_standardized_street_name']
    stype = row['Combined_Address_standardized_street_type']
    
    if pd.notna(num) and pd.notna(name) and pd.notna(stype):
        street = f"{num} {name} {stype}"
    elif pd.notna(name) and pd.notna(stype):
        street = f"{name} {stype}"
    elif pd.notna(num):
        street = str(num)
    else:
        street = "N/A"
    
    city = row['Combined_Address_standardized_city']
    state = row['Combined_Address_standardized_state']
    postal = row['Combined_Address_standardized_postal_code']
    confidence = row['Combined_Address_standardized_confidence']
    from_cache = row['Combined_Address_standardized_from_cache']
    
    print(f"{idx+1:2d}. {street}")
    print(f"    Location: {city}, {state} {postal}")
    print(f"    Original Address1: {row['Address1']}")
    print(f"    Split Info: {row['Split_Indicator']} | From Row {row['Split_From_Row']} | {row['Split_Address_Number']}")
    print(f"    Quality: Confidence={confidence}, FromCache={from_cache}")
    print()

print("=" * 130)
print("SPLIT SUMMARY:")
print("=" * 130)
split_counts = df.groupby('Split_From_Row').size()
for row_num, count in split_counts.items():
    print(f"  Original Row {row_num}: Split into {count} addresses")
