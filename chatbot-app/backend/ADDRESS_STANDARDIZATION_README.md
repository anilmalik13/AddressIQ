# Address Standardization System

This system provides AI-powered address standardization using Azure OpenAI. It takes raw, unstructured address data and converts it into a standardized format suitable for your organization's needs.

## Features

- **Intelligent Parsing**: Uses Azure OpenAI's advanced language understanding to parse complex address formats
- **Standardized Output**: Returns addresses in a consistent JSON format
- **Confidence Scoring**: Provides confidence levels for each standardization result
- **Issue Tracking**: Identifies and reports potential problems with input addresses
- **Batch Processing**: Support for processing multiple addresses at once
- **Customizable**: Configurable for organization-specific requirements

## Quick Start

### 1. Single Address Standardization

```python
from app.services.azure_openai import standardize_address

# Standardize a single address
raw_address = "123 main st apt 4b new york ny 10001"
result = standardize_address(raw_address)

print(result['formatted_address'])
# Output: "123 Main Street, Apt 4B, New York, NY 10001, USA"
```

### 2. Multiple Address Standardization

```python
from app.services.azure_openai import standardize_multiple_addresses

addresses = [
    "123 main st apt 4b new york ny 10001",
    "456 oak ave suite 200, los angeles, california 90210",
    "789 elm drive, unit 5A, chicago il 60601"
]

results = standardize_multiple_addresses(addresses)

for result in results:
    if 'error' not in result:
        print(f"Formatted: {result['formatted_address']}")
        print(f"Confidence: {result['confidence']}")
    else:
        print(f"Error: {result['error']}")
```

### 3. Custom System Prompt

```python
from app.services.azure_openai import connect_wso2, get_access_token

# Use address standardization prompt
access_token = get_access_token()
response = connect_wso2(
    access_token=access_token,
    user_content="123 main st apt 4b new york ny 10001",
    prompt_type="address_standardization"
)
```

## Output Format

The system returns addresses in this standardized JSON format:

```json
{
  "street_number": "123",
  "street_name": "Main Street",
  "street_type": "Street",
  "unit_type": "Apt",
  "unit_number": "4B",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "formatted_address": "123 Main Street, Apt 4B, New York, NY 10001, USA",
  "confidence": "high",
  "issues": []
}
```

## Confidence Levels

- **high**: All address components clearly identified and validated
- **medium**: Most components identified with minor ambiguities
- **low**: Significant missing or unclear components

## Common Issues Detected

- `missing_street_number`: Street number not found
- `unclear_street_name`: Street name is ambiguous
- `missing_city`: City information missing
- `invalid_postal_code`: Postal code format is invalid
- `ambiguous_state`: State/province unclear
- `missing_country`: Country information missing
- `incomplete_address`: Address lacks essential components

## Configuration

Customize the system for your organization by editing `app/config/address_config.py`:

```python
ADDRESS_STANDARDS = {
    "street_types": {
        "st": "Street",
        "ave": "Avenue",
        # Add your organization's preferred mappings
    },
    "validation_rules": {
        "require_country": True,
        "require_postal_code": True,
        "min_confidence_threshold": "medium"
    }
}
```

## Example Use Cases

### 1. Customer Database Cleanup
```python
# Clean up customer addresses from your database
customer_addresses = get_customer_addresses_from_db()
standardized = standardize_multiple_addresses(customer_addresses)

# Update database with standardized addresses
for i, result in enumerate(standardized):
    if result['confidence'] in ['high', 'medium']:
        update_customer_address(customer_ids[i], result['formatted_address'])
```

### 2. Mail Processing
```python
# Standardize addresses for bulk mail processing
mail_list = load_mailing_addresses()
processed_addresses = []

for address in mail_list:
    result = standardize_address(address)
    if result['confidence'] != 'low':
        processed_addresses.append(result['formatted_address'])
    else:
        # Flag for manual review
        flag_for_manual_review(address, result['issues'])
```

### 3. Real Estate Data Processing
```python
# Process property addresses from multiple sources
property_data = load_property_listings()

for property in property_data:
    standardized = standardize_address(property['raw_address'])
    property['standardized_address'] = standardized['formatted_address']
    property['address_confidence'] = standardized['confidence']
    
    # Handle low confidence addresses
    if standardized['confidence'] == 'low':
        property['requires_review'] = True
        property['address_issues'] = standardized['issues']
```

## Running the Example

To test the system with sample data:

```bash
cd /Users/AMalik13/Downloads/GitHub/AzureOpenAIConnectPOC2/chatbot-app/backend
python example_address_standardization.py
```

## Environment Variables

Make sure these are set in your `.env` file:

```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
WSO2_AUTH_URL=https://api-test.cbre.com:443/token
AZURE_OPENAI_DEPLOYMENT_ID=AOAIsharednonprodgpt35turbo16k
```

## Best Practices

1. **Batch Processing**: For large datasets, process addresses in batches to optimize API usage
2. **Error Handling**: Always check for errors in the response before using results
3. **Confidence Thresholds**: Set appropriate confidence thresholds for your use case
4. **Manual Review**: Flag low-confidence results for manual review
5. **Validation**: Consider additional validation for critical applications

## Troubleshooting

- **Authentication Issues**: Verify your CLIENT_ID and CLIENT_SECRET in the environment variables
- **Low Confidence Results**: Check if the input address has sufficient information
- **JSON Parsing Errors**: The AI occasionally returns non-JSON responses; handle these gracefully
- **Rate Limits**: Implement appropriate delays between API calls for large batches

## Support

For questions or issues with the address standardization system, please refer to the Azure OpenAI documentation or contact your system administrator.
