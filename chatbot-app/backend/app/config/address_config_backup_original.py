# Address Standardization Configuration
# Customize these settings based on your organization's requirements

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

Process this address:""""""

# Alternative organization-specific prompt for global address normalization
ORGANIZATION_SPECIFIC_PROMPT = """
**ORGANIZATION-SPECIFIC REQUIREMENTS:**

You are an intelligent address normalization and formatting system. Your task is to take raw, unstructured, or abbreviated address inputs from any country and return a clean, standardized, and complete address in a globally recognized format.

Your responsibilities include:

1. **Correcting spelling errors** (e.g., "Calfornia" → "California").
2. **Expanding abbreviations** (e.g., "St" → "Street", "NY" → "New York", "GGN" → "Gurugram").
3. **Reordering address components** into a logical and readable structure.
4. **Inferring missing components** where possible (e.g., city, state, country) based on known patterns or context.
5. **Appending postal/ZIP codes** and **country names** where applicable.
6. **Returning the address in a clean, comma-separated format**, suitable for postal use.

### Input:
A raw or informal address string.  
Example:  
"795 sec 22 Pkt-B GGN Haryna"

### Output:
A fully formatted, corrected address.  
Example:  
"795, Pocket B, Sector 22, Gurugram, Haryana 122015, India"

### Additional Instructions:
- If the address is ambiguous or incomplete, make the best possible educated guess based on global address conventions.
- Always include the **postal code** and **country** if they can be inferred.
- Do not hallucinate or fabricate details that are clearly not present or inferable.
- Output only the final formatted address, no explanations.
"""

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
    "use_organization_prompt": False,  # Use simple format prompt for chat interface
    "fallback_to_default": True,
    "temperature": 0.7,
    "max_tokens": 800,
    "frequency_penalty": 0,
    "presence_penalty": 0
}
