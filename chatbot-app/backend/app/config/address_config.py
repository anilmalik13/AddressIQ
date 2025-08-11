# Address Standardization Configuration
# Optimized version with concise, effective prompts

# System prompts for different use cases
ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system. Parse the raw address data and return it in standardized JSON format.

**CORE CAPABILITIES:**
- Global address parsing (195+ countries)
- Spelling correction and abbreviation expansion  
- Component extraction and validation
- Country-specific formatting standards
- Postal code validation and formatting

**JSON OUTPUT FORMAT:**
```json
{
  "street_number": "123",
  "street_name": "Main Street", 
  "street_type": "Street",
  "unit_type": "Suite",
  "unit_number": "100",
  "building_name": null,
  "floor_number": null,
  "city": "New York",
  "state": "NY",
  "county": null,
  "postal_code": "10001",
  "country": "USA",
  "country_code": "USA",
  "district": null,
  "region": null,
  "suburb": null,
  "locality": null,
  "sublocality": null,
  "canton": null,
  "prefecture": null,
  "oblast": null,
  "formatted_address": "123 Main Street, Suite 100, New York, NY 10001, USA",
  "confidence": "high",
  "issues": [],
  "address_type": "residential",
  "po_box": null,
  "delivery_instructions": null,
  "mail_route": null
}
```

**RULES:**
1. Return ONLY valid JSON - no explanations
2. Use appropriate country-specific formatting in formatted_address
3. Set confidence: "high" (complete), "medium" (minor issues), "low" (major issues)
4. List specific issues in issues array if any problems found
5. Standardize abbreviations (St→Street, NY→New York, etc.)
6. Correct common spelling errors
7. Use proper postal code formats by country

Process this address:"""

# Alternative organization-specific prompt for global address normalization
ORGANIZATION_SPECIFIC_PROMPT = """You are an intelligent address normalization system. Take raw address inputs and return clean, standardized addresses.

**TASKS:**
1. Correct spelling errors
2. Expand abbreviations  
3. Reorder components logically
4. Infer missing components where possible
5. Apply country-specific formatting

**INPUT:** Raw address string
**OUTPUT:** Fully formatted address only, no explanations

Example: "795 sec 22 Pkt-B GGN Haryna" → "795, Pocket B, Sector 22, Gurugram, Haryana 122015, India"
"""

# Batch processing prompt for multiple addresses
BATCH_ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system. Process multiple raw addresses and return them in standardized JSON format.

**CORE CAPABILITIES:**
- Global address parsing (195+ countries)
- Spelling correction and abbreviation expansion  
- Component extraction and validation
- Country-specific formatting standards
- Postal code validation and formatting

**BATCH OUTPUT FORMAT:**
Return a JSON array where each object represents one standardized address:
```json
[
  {
    "input_index": 0,
    "street_number": "123",
    "street_name": "Main Street", 
    "street_type": "Street",
    "unit_type": "Suite",
    "unit_number": "100",
    "building_name": null,
    "floor_number": null,
    "city": "New York",
    "state": "NY",
    "county": null,
    "postal_code": "10001",
    "country": "USA",
    "country_code": "USA",
    "district": null,
    "region": null,
    "suburb": null,
    "locality": null,
    "sublocality": null,
    "canton": null,
    "prefecture": null,
    "oblast": null,
    "formatted_address": "123 Main Street, Suite 100, New York, NY 10001, USA",
    "confidence": "high",
    "issues": [],
    "address_type": "residential",
    "po_box": null,
    "delivery_instructions": null,
    "mail_route": null
  }
]
```

**RULES:**
1. Return ONLY valid JSON array - no explanations
2. Use input_index to match each result to input address (0-based)
3. Use appropriate country-specific formatting in formatted_address
4. Set confidence: "high" (complete), "medium" (minor issues), "low" (major issues)
5. List specific issues in issues array if any problems found
6. Standardize abbreviations (St→Street, NY→New York, etc.)
7. Correct common spelling errors
8. Use proper postal code formats by country

Process these addresses:"""

# Country-specific formatting rules
COUNTRY_FORMATS = {
    "USA": {
        "format": "{street_number} {street_name} {street_type}, {unit_type} {unit_number}, {city}, {state} {postal_code}, {country}",
        "example": "123 Main Street, Suite 100, New York, NY 10001, USA"
    },
    "UK": {
        "format": "{street_number} {street_name}, {unit_type} {unit_number}, {city}, {postal_code}, {country}",
        "example": "123 High Street, Flat 4A, London, SW1A 1AA, United Kingdom"
    },
    "India": {
        "format": "{street_number}, {street_name}, {unit_type} {unit_number}, {locality}, {city}, {district}, {state} {postal_code}, {country}",
        "example": "123, MG Road, Flat 2B, Koramangala, Bangalore, Bangalore Urban, Karnataka 560001, India"
    },
    "Germany": {
        "format": "{street_name} {street_number}, {unit_type} {unit_number}, {postal_code} {city}, {country}",
        "example": "Hauptstraße 123, Wohnung 4A, 10115 Berlin, Germany"
    },
    "Australia": {
        "format": "{unit_type} {unit_number}/{street_number} {street_name}, {suburb}, {city} {state} {postal_code}, {country}",
        "example": "Unit 4/123 Collins Street, Melbourne VIC 3000, Australia"
    },
    "France": {
        "format": "{street_number} {street_name}, {unit_type} {unit_number}, {postal_code} {city}, {country}",
        "example": "123 Rue de la Paix, Appartement 4A, 75001 Paris, France"
    },
    "Canada": {
        "format": "{street_number} {street_name} {street_type}, {unit_type} {unit_number}, {city}, {state} {postal_code}, {country}",
        "example": "123 Main Street, Suite 100, Toronto, ON M5V 3A8, Canada"
    },
    "Japan": {
        "format": "{prefecture}, {city}, {district}, {street_name} {street_number}, {unit_type} {unit_number}, {postal_code}, {country}",
        "example": "Tokyo, Shibuya, Harajuku, Takeshita Street 123, Apartment 4A, 150-0001, Japan"
    },
    "Brazil": {
        "format": "{street_name}, {street_number}, {unit_type} {unit_number}, {district}, {city} - {state}, {postal_code}, {country}",
        "example": "Rua Augusta, 123, Apartamento 4A, Centro, São Paulo - SP, 01305-100, Brazil"
    }
}

def get_country_specific_prompt(target_country=None):
    """Generate country-specific formatting instructions"""
    if target_country and target_country.upper() in COUNTRY_FORMATS:
        country_format = COUNTRY_FORMATS[target_country.upper()]
        format_instruction = f"""
**TARGET COUNTRY**: {target_country.upper()}
**REQUIRED FORMAT**: Use {target_country} standard formatting in the formatted_address field.
**FORMAT PATTERN**: {country_format['format']}
**EXAMPLE OUTPUT**: {country_format['example']}

Apply {target_country} specific formatting rules and populate all relevant geographic components.
"""
    else:
        format_instruction = """
**FLEXIBLE FORMAT**: Detect the country from address components and use appropriate local formatting convention.
"""
    
    return format_instruction

# Prompt configuration settings
PROMPT_CONFIG = {
    "use_address_standardization_prompt": True,  # Use JSON-based prompt for CSV processing
    "use_organization_prompt": False,  # Use simple format prompt for address processing interface
    "fallback_to_default": True,
    "temperature": 0.7,
    "max_tokens": 1500,  # Increased for batch processing
    "frequency_penalty": 0,
    "presence_penalty": 0,
    # Batch processing settings
    "batch_size": 10,  # Number of addresses to process in one API call
    "enable_batch_processing": True  # Enable batch processing for CSV operations
}
