# Address Splitting Feature Documentation

## Overview

The Address Splitting feature is an optional enhancement to AddressIQ that intelligently splits addresses containing multiple addresses into separate records. This feature analyzes addresses using **rule-based logic** or **GPT-based AI analysis** and creates additional rows in the output when appropriate, while maintaining all standardization functionality.

## Key Features

- **Dual-mode operation**: Choose between rule-based (fast, deterministic) or GPT-based (intelligent, context-aware) splitting
- **Non-destructive**: Original functionality remains unchanged; splitting is opt-in via `--enable-split` flag
- **Metadata tracking**: Adds columns to track which rows were split and their relationships
- **Full standardization**: Each split address is fully standardized like any other address
- **Flexible**: Can switch between modes based on accuracy vs. performance needs

## Splitting Modes

### 1. Rule-Based Splitting (Default)
- **Fast**: No API calls for split detection
- **Deterministic**: Same input always produces same output
- **Pattern-based**: Uses regular expressions and patterns
- **No additional cost**: Only standardization uses API

### 2. GPT-Based Splitting (Optional)
- **Intelligent**: Uses AI to understand context
- **Handles edge cases**: Better at ambiguous situations
- **Learns from patterns**: Can adapt to unusual formats
- **API usage**: Uses Azure OpenAI for split analysis
- **Enable with**: `--use-gpt-split` flag

## How It Works

### 1. Detection Rules

The splitter applies the following rules to determine if an address should be split:

#### NO SPLIT Rules (takes precedence)

The following address patterns will **NOT** be split:

1. **Range of street numbers**: e.g., "211-245 Wheelhouse Lane", "96-100 Pane Road"
2. **Fractional identifiers**: Contains Apt, Ste, Unit, #, Floor, etc.
   - Example: "3800 West Ray Road Unit B3 (B15-B20)"
   - Example: "6120 & 6132 Brookshire Blvd, Units M, N & F"
3. **Multiple fractional units without identifiers**: e.g., "140 Vann St NE, 1st Floor - 310/320"
4. **Directional identifiers**: NEQ, SWC, NEC, east of, south of, between, intersection, etc.
   - Example: "W/L of S. Rangerville Road, SW of S. Expressway 83"
   - Example: "NEQ OF THE SEQ OF SECTION 26, TOWNSHIP 15 SOUTH, RANGE 67 WEST OF THE 6TH P.M."
5. **No street numbers**: e.g., "Highway 40 and K", "Main Street (Hwy 20)"

#### POTENTIAL SPLIT Rules

Addresses will be split if they meet the following criteria:

1. **Contains "and" or "&" with commas**: 
   - Example: "5250 NW 86th St, 8651, 8751, 8801 Northpark Dr"
   - Result: 4 separate addresses with the street name applied to standalone numbers
   
2. **Contains "and" or "&" without special characters**:
   - Example: "34 Fairview St and 45 Oakwood Ave"
   - Example: "10659 West Fairview Avenue & 1421 North Five Mile Road"
   
3. **Address1 and Address2 fields contain separate addresses**:
   - Example: Address1="2504 and 2506 Zeppelin Rd", Address2="2510 and 2520 Aviation Way"

### 2. Splitting Logic

When an address is determined to be splittable:

1. The address is parsed and split at "and" or "&" boundaries
2. For comma-separated addresses, the system intelligently:
   - Identifies the base address with a complete street name
   - Applies the street name to standalone numbers
   - Creates individual addresses for each component
3. Each resulting address becomes a new row in the output

### 3. Output Structure

When splitting occurs, the output includes additional metadata columns:

- **Split_Indicator**: "Yes" if the row is a result of splitting, "No" otherwise
- **Split_From_Row**: Original row number that was split
- **Split_Address_Number**: E.g., "1 of 3", "2 of 3", "3 of 3"

All standard address standardization columns are preserved and populated for each split address.

## Usage

### Command Line

#### Basic Usage with Split Enabled (Rule-Based)

```bash
# Process a CSV file with rule-based splitting (default)
python csv_address_processor.py addresses.csv --enable-split

# Process with GPT-based splitting
python csv_address_processor.py addresses.csv --enable-split --use-gpt-split

# Process with specific output file
python csv_address_processor.py addresses.csv -o output.csv --enable-split

# Batch process all files in inbound directory with GPT splitting
python csv_address_processor.py --batch-process --enable-split --use-gpt-split

# Process with specific address column
python csv_address_processor.py addresses.csv -c "full_address" --enable-split

# Process with combined columns
python csv_address_processor.py addresses.csv --address-columns "street,city,state" --enable-split
```

#### Combined with Other Options

```bash
# With custom batch size
python csv_address_processor.py addresses.csv --enable-split --batch-size 10

# With GPT splitting and custom batch size
python csv_address_processor.py addresses.csv --enable-split --use-gpt-split --batch-size 10

# Without free API enhancement
python csv_address_processor.py addresses.csv --enable-split --no-free-apis

# With custom base directory
python csv_address_processor.py --batch-process --enable-split --base-dir /path/to/folder
```

### Python API

```python
from csv_address_processor import CSVAddressProcessor

# Initialize processor
processor = CSVAddressProcessor()

# Process with rule-based splitting (default)
output_file = processor.process_csv_file(
    input_file="addresses.csv",
    output_file="output.csv",
    enable_split=True,
    use_gpt_split=False,  # Rule-based (default)
    use_free_apis=True,
    batch_size=10
)

# Process with GPT-based splitting
output_file = processor.process_csv_file(
    input_file="addresses.csv",
    output_file="output.csv",
    enable_split=True,
    use_gpt_split=True,  # GPT-based
    use_free_apis=True,
    batch_size=10
)
```

### Standalone Address Splitter

You can also use the splitter independently:

```python
from address_splitter import AddressSplitter

# Rule-based splitter
splitter = AddressSplitter(use_gpt=False)

# GPT-based splitter
splitter_gpt = AddressSplitter(use_gpt=True)

# Analyze a single address
result = splitter.analyze_and_split(
    address1="34 Fairview St and 45 Oakwood Ave",
    address2=None
)

print(f"Should split: {result['should_split']}")
print(f"Method used: {result['method_used']}")
print(f"Reason: {result['split_reason']}")
print(f"Split addresses: {result['addresses']}")

# Test the splitter
if __name__ == "__main__":
    from address_splitter import test_splitter
    
    # Test with rule-based
    test_splitter(use_gpt=False)
    
    # Test with GPT-based
    test_splitter(use_gpt=True)
```

## Examples

### Example 1: Comma-separated addresses with street numbers

**Input:**
```
Address: 5250 NW 86th St, 8651, 8751, 8801 Northpark Dr
```

**Output (4 rows):**
```
Row 1: 5250 NW 86th St (Split_Indicator: Yes, Split_Address_Number: 1 of 4)
Row 2: 8651 Northpark Dr (Split_Indicator: Yes, Split_Address_Number: 2 of 4)
Row 3: 8751 Northpark Dr (Split_Indicator: Yes, Split_Address_Number: 3 of 4)
Row 4: 8801 Northpark Dr (Split_Indicator: Yes, Split_Address_Number: 4 of 4)
```

Each row is then standardized individually.

### Example 2: Simple "and" separated addresses

**Input:**
```
Address: 34 Fairview St and 45 Oakwood Ave
```

**Output (2 rows):**
```
Row 1: 34 Fairview St (Split_Indicator: Yes, Split_Address_Number: 1 of 2)
Row 2: 45 Oakwood Ave (Split_Indicator: Yes, Split_Address_Number: 2 of 2)
```

### Example 3: Address with units (NO SPLIT)

**Input:**
```
Address: 6120 & 6132 Brookshire Blvd, Units M, N & F
```

**Output (1 row):**
```
Row 1: 6120 & 6132 Brookshire Blvd, Units M, N & F (Split_Indicator: No)
```

This address is NOT split because it contains fractional identifiers (Units).

### Example 4: Range of street numbers (NO SPLIT)

**Input:**
```
Address: 211-245 Wheelhouse Lane
```

**Output (1 row):**
```
Row 1: 211-245 Wheelhouse Lane (Split_Indicator: No)
```

This address is NOT split because it contains a range of street numbers.

## Output File Structure

When splitting is enabled, the output CSV includes:

### Original Columns
All columns from the input CSV are preserved.

### Splitting Metadata Columns
- `Split_Indicator`: "Yes" or "No"
- `Split_From_Row`: Original row number (for split rows)
- `Split_Address_Number`: Position indicator (e.g., "1 of 3")

### Standardization Columns (for each address column processed)
- `<column>_standardized_formatted`
- `<column>_standardized_street_number`
- `<column>_standardized_street_name`
- `<column>_standardized_street_type`
- `<column>_standardized_unit_type`
- `<column>_standardized_unit_number`
- `<column>_standardized_city`
- `<column>_standardized_state`
- `<column>_standardized_postal_code`
- `<column>_standardized_country`
- ... and many more standardization fields

## Testing

### Test the Splitter Module

```bash
# Run the built-in test suite
python address_splitter.py
```

This will run through all the example cases from the requirements and show pass/fail results.

### Test with Sample CSV

Create a test CSV file (`test_addresses.csv`):

```csv
address
211-245 Wheelhouse Lane
5250 NW 86th St, 8651, 8751, 8801 Northpark Dr
34 Fairview St and 45 Oakwood Ave
6120 & 6132 Brookshire Blvd, Units M, N & F
Highway 40 and K
```

Run the processor:

```bash
python csv_address_processor.py test_addresses.csv --enable-split -o results.csv
```

Check the output to verify splitting behavior.

## Performance Considerations

- **Row Expansion**: Files with many splittable addresses will result in more rows in the output
- **Processing Time**: Each split address is standardized individually, which may increase processing time
- **Memory Usage**: Larger output files require more memory
- **Batch Processing**: Use appropriate batch sizes (`--batch-size`) to optimize performance

## Best Practices

1. **Test First**: Run on a small sample of your data first to verify behavior
2. **Review Split Decisions**: Check the `Split_Indicator` column to see which addresses were split
3. **Preserve Originals**: The original row number is tracked in `Split_From_Row`
4. **Use Selectively**: Only enable splitting when needed for your use case
5. **Combine with Other Features**: Splitting works seamlessly with all other AddressIQ features

## Troubleshooting

### Issue: Addresses not splitting as expected

**Solution**: Check if the address matches a "NO SPLIT" rule. Review the detection rules above.

### Issue: Too many addresses being split

**Solution**: Review your input data. The feature may be detecting patterns you didn't intend. Consider preprocessing to remove commas or "and" where they don't indicate multiple addresses.

### Issue: Performance degradation

**Solution**: 
- Reduce batch size with `--batch-size` parameter
- Process smaller files
- Disable free API enhancement with `--no-free-apis` if not needed

## Architecture

### Module: `address_splitter.py`

**Class: `AddressSplitter`**

Key methods:
- `should_not_split(address)`: Checks NO SPLIT rules
- `detect_potential_split(address1, address2)`: Checks POTENTIAL SPLIT rules
- `split_address(address1, address2)`: Performs the actual split
- `analyze_and_split(address1, address2)`: Main entry point with full analysis

### Module: `csv_address_processor.py`

**Modifications:**
- Added `address_splitter` as an optional component
- New method: `apply_address_splitting(df, address_columns)` - Applies splitting to dataframe
- Updated all processing methods to accept `enable_split` parameter
- Added `--enable-split` command-line argument

## Version History

- **v1.0** (January 2026): Initial release of address splitting feature
  - Rule-based splitting logic
  - Integration with CSV processor
  - Metadata tracking
  - Full test coverage

## Support

For issues, questions, or contributions related to the address splitting feature:
1. Check the examples in this documentation
2. Run the test suite: `python address_splitter.py`
3. Review the code comments in `address_splitter.py`
4. Check existing functionality without `--enable-split` to isolate the issue

## Future Enhancements

Potential future improvements:
- Additional detection rules based on feedback
- Configurable rules via configuration file
- Machine learning-based split detection
- Interactive mode to review split decisions
- Split confidence scores
