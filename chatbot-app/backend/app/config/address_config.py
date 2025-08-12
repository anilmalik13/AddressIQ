# Address Standardization Configuration
# Optimized version with concise, effective prompts

# System prompts for different use cases
ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system.
Return a single raw JSON object only (no markdown, no code fences, no text).

TASKS:
- Expand abbreviations, fix misspellings.
- Extract components and validate.
- Apply country-specific formatting.
- Validate postal codes by country; do not fabricate unknowns.
- Normalize casing: Title Case for names; country-specific state/province codes; proper postal code formats.

OUTPUT SCHEMA (all keys must be present; use null for unknowns):
{
  "street_number": null,
  "street_name": null,
  "street_type": null,
  "unit_type": null,
  "unit_number": null,
  "building_name": null,
  "floor_number": null,
  "city": null,
  "state": null,
  "county": null,
  "postal_code": null,
  "country": null,
  "country_code": null,         // ISO 3166-1 alpha-3 (e.g., USA, IND, GBR, DEU)
  "district": null,
  "region": null,
  "suburb": null,
  "locality": null,
  "sublocality": null,
  "canton": null,
  "prefecture": null,
  "oblast": null,
  "formatted_address": "",
  "confidence": "unknown",      // high | medium | low | unknown
  "issues": [],                 // list specific problems, e.g., ["postal_code_missing", "ambiguous_city"]
  "address_type": null,         // residential | commercial | po_box | other
  "po_box": null,
  "delivery_instructions": null,
  "mail_route": null
}

RULES:
1) Output only valid JSON for the object above (no extra text).
2) Use country-specific formatting for formatted_address.
3) If a component is missing or unverifiable, set it to null and add a clear issue.
4) Never invent postal codes; leave null and add "postal_code_missing".
5) Prefer a provided target country if present; otherwise auto-detect.
6) Standardize abbreviations (St→Street, Ave→Avenue, Rd→Road, etc.).
7) If uncertainty remains, set confidence to low/medium and explain in issues.

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
BATCH_ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system.
Return a raw JSON array only (no markdown, no code fences, no text).
Each element must be a JSON object with this schema and include "input_index" and "original_address".

OBJECT SCHEMA (all keys present; null for unknowns):
{
  "input_index": 0,
  "original_address": "",
  "street_number": null,
  "street_name": null,
  "street_type": null,
  "unit_type": null,
  "unit_number": null,
  "building_name": null,
  "floor_number": null,
  "city": null,
  "state": null,
  "county": null,
  "postal_code": null,
  "country": null,
  "country_code": null,         // ISO 3166-1 alpha-3
  "district": null,
  "region": null,
  "suburb": null,
  "locality": null,
  "sublocality": null,
  "canton": null,
  "prefecture": null,
  "oblast": null,
  "formatted_address": "",
  "confidence": "unknown",
  "issues": [],
  "address_type": null,
  "po_box": null,
  "delivery_instructions": null,
  "mail_route": null
}

RULES:
1) Output only a valid JSON array of objects (no extra text).
2) Preserve input order using input_index (0-based).
3) Include original_address verbatim per item.
4) Apply country-specific formatting; prefer provided target country; otherwise auto-detect.
5) Never fabricate postal codes; use null and add "postal_code_missing".
6) Use standardized abbreviations and spelling corrections.
7) Set confidence to high | medium | low | unknown, and list issues precisely.

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
    "use_organization_prompt": False,           # Keep disabled
    "fallback_to_default": True,
    # More deterministic outputs
    "temperature": 0.2,
    "max_tokens": 1200,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    # Batch processing settings
    "batch_size": 10,
    "enable_batch_processing": True
}
