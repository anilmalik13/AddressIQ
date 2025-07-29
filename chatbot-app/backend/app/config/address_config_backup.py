# Address Standardization Configuration
# Customize these settings based on your organization's requirements

ADDRESS_STANDARDS = {
    # Define your organization's preferred address formats
    "street_types": {
        "st": "Street",
        "ave": "Avenue", 
        "blvd": "Boulevard",
        "rd": "Road",
        "dr": "Drive",
        "ln": "Lane",
        "ct": "Court",
        "pl": "Place",
        "way": "Way",
        "cir": "Circle",
        "pkwy": "Parkway"
    },
    
    "unit_types": {
        "apt": "Apt",
        "apartment": "Apt",
        "suite": "Suite",
        "ste": "Suite",
        "unit": "Unit",
        "floor": "Floor",
        "fl": "Floor",
        "room": "Room",
        "rm": "Room",
        "building": "Bldg",
        "bldg": "Bldg"
    },
    
    "directionals": {
        "north": "N",
        "south": "S", 
        "east": "E",
        "west": "W",
        "northeast": "NE",
        "northwest": "NW",
        "southeast": "SE",
        "southwest": "SW"
    },
    
    # Define which countries your organization operates in
    "supported_countries": ["USA", "CAN", "MEX", "GBR"],
    
    # State/Province mappings for your regions
    "state_mappings": {
        # US States
        "california": "CA",
        "new york": "NY",
        "texas": "TX",
        "florida": "FL",
        # Add more as needed for your organization
        
        # Canadian Provinces
        "ontario": "ON",
        "british columbia": "BC",
        "quebec": "QC"
        # Add more as needed
    },
    
    # Organization-specific address validation rules
    "validation_rules": {
        "require_country": True,
        "require_postal_code": True,
        "allow_po_boxes": True,
        "min_confidence_threshold": "medium"
    }
}

# Dynamic prompt generation function
def get_dynamic_address_prompt():
    """
    Generate organization-specific address standardization prompt based on ADDRESS_STANDARDS
    """
    street_types_list = ", ".join(ADDRESS_STANDARDS["street_types"].values())
    unit_types_list = ", ".join(ADDRESS_STANDARDS["unit_types"].values()) 
    directionals_list = ", ".join(ADDRESS_STANDARDS["directionals"].values())
    supported_countries_list = ", ".join(ADDRESS_STANDARDS["supported_countries"])
    
    return f"""You are an expert address standardization system. Your task is to take raw, unstructured address data and convert it into a standardized format following these organization-specific guidelines:

**STANDARDIZATION RULES:**

1. **Format Structure**: Return addresses in this exact JSON format:
   ```json
   {{
     "street_number": "123",
     "street_name": "Main Street",
     "street_type": "Street",
     "unit_type": "Suite",
     "unit_number": "100",
     "city": "New York",
     "state": "NY",
     "postal_code": "10001",
     "country": "USA",
     "formatted_address": "123 Main Street, Suite 100, New York, NY 10001, USA",
     "confidence": "high",
     "issues": []
   }}
   ```

2. **Street Types**: Standardize to these preferred forms: {street_types_list}

3. **Directionals**: Use these standard abbreviations: {directionals_list}

4. **Unit Types**: Standardize to these forms: {unit_types_list}

5. **Supported Countries**: Focus on these regions: {supported_countries_list}

6. **State/Province**: Use official 2-letter codes (NY, CA, TX, ON, BC, etc.)

7. **Postal Codes**: Format according to country standards (US: 12345 or 12345-6789, CA: A1A 1A1)

**CONFIDENCE LEVELS:**
- "high": All components clearly identified and validated
- "medium": Most components identified, minor ambiguities
- "low": Significant missing or unclear components

**ISSUE TRACKING:**
Report any problems in the "issues" array:
- "missing_street_number"
- "unclear_street_name" 
- "missing_city"
- "invalid_postal_code"
- "ambiguous_state"
- "missing_country"
- "incomplete_address"

**SPECIAL HANDLING:**
- If PO Box, format as: "PO Box 123"
- For rural routes: "RR 1" or "Rural Route 1"
- For military addresses: Use APO/FPO/DPO format
- Handle international addresses appropriately
- Preserve apartment/suite information accurately

**RESPONSE REQUIREMENTS:**
- Always respond with valid JSON only
- Do not include explanations outside the JSON
- If address cannot be parsed, set confidence to "low" and list all issues
- Maintain original intent while standardizing format

Process the following address data and return the standardized result:"""

# System prompts for different use cases
ADDRESS_STANDARDIZATION_PROMPT = get_dynamic_address_prompt()

**CONFIDENCE LEVELS:**
- "high": All components clearly identified and validated
- "medium": Most components identified, minor ambiguities
- "low": Significant missing or unclear components

**ISSUE TRACKING:**
Report any problems in the "issues" array:
- "missing_street_number"
- "unclear_street_name" 
- "missing_city"
- "invalid_postal_code"
- "ambiguous_state"
- "missing_country"
- "incomplete_address"

**SPECIAL HANDLING:**
- If PO Box, format as: "PO Box 123"
- For rural routes: "RR 1" or "Rural Route 1"
- For military addresses: Use APO/FPO/DPO format
- Handle international addresses appropriately
- Preserve apartment/suite information accurately

**RESPONSE REQUIREMENTS:**
- Always respond with valid JSON only
- Do not include explanations outside the JSON
- If address cannot be parsed, set confidence to "low" and list all issues
- Maintain original intent while standardizing format

Process the following address data and return the standardized result:"""

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
