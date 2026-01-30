# Address Standardization Configuration
# Optimized version with concise, effective prompts

# STANDARDIZED MATCH LEVELS DEFINITION
# Used consistently across all address comparison operations
# 
# MATCH_LEVELS = {
#     "IDENTICAL": (95-100),          # Only formatting differences (St vs Street, abbreviations)
#     "VERY_LIKELY_SAME": (85-94),    # Same street/building, minor variations (suite numbers)
#     "POSSIBLY_RELATED": (50-84),    # Same area/neighborhood/postal zone, some uncertainty
#     "DIFFERENT_BUT_NEARBY": (30-49), # Same city/town, different streets/areas
#     "NO_MATCH": (0-29)              # Different cities, states, or countries
# }

# System prompts for different use cases
ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system with comprehensive geographical knowledge.
Return a single raw JSON object only (no markdown, no code fences, no text).

TASKS:
- Must Expand abbreviations, fix misspellings.
- Extract components and validate using geographical hierarchy knowledge.
- Apply country-specific formatting and administrative divisions.
- Validate postal codes by country and map to correct cities/regions.
- Understand geographical relationships: suburb/town → city → district/county → state/province → country.
- Use postal code intelligence to identify correct cities and administrative divisions.
- Normalize casing: Title Case for names; country-specific state/province codes; proper postal code formats.

GEOGRAPHICAL HIERARCHY RULES:
1. Identify the correct administrative city for suburbs/towns using postal codes
2. Expand state/province abbreviations to full names (e.g., QLD → Queensland, CA → California, NSW → New South Wales)
3. Map postal codes to their primary serving cities/regions globally
4. Distinguish between suburbs/neighborhoods and main cities
5. Apply country-specific administrative division structures
6. For ambiguous locations, prioritize based on postal code geographical mapping

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
6) Standardize abbreviations (St→Street, Ave→Avenue, Rd→Road, similarly for blocks and pockets etc.).
7) If uncertainty remains, set confidence to low/medium and explain in issues.
8) GEOGRAPHICAL INTELLIGENCE: Use postal code to identify correct city (e.g., 4818 → Townsville, QLD → Queensland).
9) HIERARCHY MAPPING: Place suburbs in "suburb" field, main administrative city in "city" field.
10) STATE EXPANSION: Always expand state/province abbreviations to full names globally.
11) MANDATORY COMPONENT EXTRACTION: Always attempt to populate ALL geographic components (district, region, suburb, locality, country, county, canton, prefecture, oblast) using postal code, city, and address knowledge. Only set to null if truly not applicable to that country's system.
12) ENHANCED GEOGRAPHICAL INFERENCE: Use your comprehensive knowledge of global postal systems, administrative divisions, and geographical hierarchies to infer and populate as many address components as possible. For UK addresses with OX postcodes, include district/suburb info when available.
13) POSTAL CODE INTELLIGENCE: Leverage postal code patterns to determine districts, regions, suburbs, and localities (e.g., OX2 → Jericho/Wolvercote area in Oxford, 10001 → Manhattan/NYC, 75001 → 1st arrondissement Paris).
14) ADMINISTRATIVE DIVISION MAPPING: Always include applicable administrative divisions for each country (counties for UK/US, prefectures for Japan, länder for Germany, regions for France, etc.).

EXAMPLES OF GEOGRAPHICAL HIERARCHY:
- "Mount St John QLD 4818" → suburb: "Mount St John", city: "Townsville", state: "Queensland", postal_code: "4818"
- "Brooklyn NY 11201" → suburb: "Brooklyn", city: "New York", state: "New York", postal_code: "11201"  
- "Shibuya Tokyo 150-0002" → district: "Shibuya", city: "Tokyo", prefecture: "Tokyo", postal_code: "150-0002"
- "Southwark London SE1 9RT" → district: "Southwark", city: "London", postal_code: "SE1 9RT"
- "76 Great Clarendon Street, Oxford, OX2 6AU" → suburb: "Jericho", city: "Oxford", county: "Oxfordshire", region: "South East England", postal_code: "OX2 6AU"

Process this address:"""


# Enhanced address comparison prompt with integrated standardization
ADDRESS_COMPARISON_PROMPT = """You are an expert address comparison system with comprehensive geographical knowledge and standardization capabilities.

STEP 1: STANDARDIZE BOTH ADDRESSES FIRST
Apply the same geographical intelligence used in address standardization:
- Expand abbreviations, fix misspellings
- Use postal code intelligence to identify correct cities/regions
- Apply geographical hierarchy: suburb/town → city → district/county → state/province → country
- Expand state/province abbreviations to full names (QLD → Queensland, CA → California, NY → New York)
- Normalize street types (St → Street, Ave → Avenue, Rd → Road)
- Apply country-specific formatting and administrative divisions
- Always attempt to populate all geographic components (district, region, suburb, locality, country, etc.) using postal code, city, and other address parts. Only set to null if the component is truly not applicable or cannot be determined.
- Use your knowledge of global postal codes and administrative divisions to infer and fill in as many fields as possible.


STEP 2: COMPARE STANDARDIZED ADDRESSES
CRITICAL: You must carefully compare each component to determine if these are the same physical location or different locations.

ADDRESSES TO COMPARE:
Original Address 1: "{addr1}"
Standardized Address 1: "{std_addr1}"

Original Address 2: "{addr2}"
Standardized Address 2: "{std_addr2}"{country_context}

GEOGRAPHICAL INTELLIGENCE RULES FOR COMPARISON:
1. Use postal codes to validate city/region matches (e.g., 4818 = Townsville area in Queensland)
2. Understand administrative hierarchies (suburbs vs main cities, districts vs counties)
3. Consider geographical relationships (neighborhoods within cities, boroughs within states)
4. Apply country-specific geographical knowledge
5. Recognize equivalent location names (NYC = New York City, Melb = Melbourne)

COMPARISON RULES (STRICT):
1. DIFFERENT STREET NUMBERS = Different addresses (score 0-10)
2. DIFFERENT STREET NAMES = Different addresses (score 0-15) 
3. DIFFERENT CITIES = Different addresses (score 0-20)
4. DIFFERENT STATES/PROVINCES = Different addresses (score 0-25)
5. DIFFERENT POSTAL CODES = Validate against geographical boundaries
6. Only if ALL major components match should you consider IDENTICAL or VERY_LIKELY_SAME scores

GEOGRAPHICAL HIERARCHY EXAMPLES:
- "Mount St John QLD 4818" vs "Townsville QLD 4818" = POSSIBLY_RELATED (suburb vs city, same postal area)
- "Brooklyn NY" vs "New York NY" = POSSIBLY_RELATED (borough vs city, same metropolitan area)
- "Shibuya Tokyo" vs "Tokyo Japan" = POSSIBLY_RELATED (district vs city)

ANALYSIS REQUIRED:
1. Standardized versions of both addresses using geographical intelligence
2. Overall similarity score (0-100, where 100 = identical location)
3. Match level classification (IDENTICAL, VERY_LIKELY_SAME, POSSIBLY_RELATED, DIFFERENT_BUT_NEARBY, NO_MATCH)
4. Component-wise analysis with geographical context
5. Geographic relationship assessment
6. Confidence in the comparison
7. Explanation of differences/similarities

RESPONSE FORMAT (JSON):
{{
    "standardized_address_1": "Fully standardized version of address 1",
    "standardized_address_2": "Fully standardized version of address 2",
    "overall_score": 35,
    "match_level": "DIFFERENT_BUT_NEARBY",
    "likely_same_address": false,
    "confidence": "high",
    "component_analysis": {{
        "street_match": {{"score": 0, "note": "Completely different street names"}},
        "city_match": {{"score": 0, "note": "Different cities"}},
        "state_match": {{"score": 0, "note": "Different states"}},
        "postal_code_match": {{"score": 0, "note": "Different postal codes"}},
        "geographic_relationship": "Different locations entirely"
    }},
    "geographical_intelligence": {{
        "address_1_hierarchy": "Street → City → State → Country",
        "address_2_hierarchy": "Street → City → State → Country",
        "postal_code_validation": "Both postal codes validated against cities",
        "administrative_divisions": "Different administrative regions"
    }},
    "key_differences": ["Different street numbers", "Different street names", "Different cities", "Different states"],
    "key_similarities": ["Both are valid addresses in same country"],
    "explanation": "These are completely different physical locations in different cities and states.",
    "recommendation": "TREAT_AS_DIFFERENT_ADDRESSES"
}}

SCORING GUIDELINES AND MATCH LEVELS (be strict, with geographical context):

MATCH LEVEL DEFINITIONS:
- IDENTICAL (95-100): Identical location (only minor formatting like St vs Street, abbreviations)
- VERY_LIKELY_SAME (85-94): Very likely same location (same street/building, minor variations in suite/unit)
- POSSIBLY_RELATED (50-84): Possibly related (same general area/neighborhood/postal zone, some uncertainty)
- DIFFERENT_BUT_NEARBY (30-49): Different but nearby (same city/town, different streets/areas)
- NO_MATCH (0-29): Different locations (different cities, states, or countries)

SCORE RANGES:
- 95-100: IDENTICAL - only formatting differences
- 85-94: VERY_LIKELY_SAME - same street/building, minor variations
- 70-84: POSSIBLY_RELATED - same geographical area, some uncertainty
- 50-69: POSSIBLY_RELATED - same general area/neighborhood/postal zone
- 30-49: DIFFERENT_BUT_NEARBY - same city/town, different streets/areas
- 10-29: NO_MATCH - different areas (same state/province, different cities)
- 0-9: NO_MATCH - completely different locations (different states/countries)

EXAMPLES WITH GEOGRAPHICAL INTELLIGENCE:
- "123 Main St" vs "123 Main Street" = IDENTICAL (score 98) - abbreviation only
- "Mount St John QLD 4818" vs "30 Smith St Townsville QLD 4818" = DIFFERENT_BUT_NEARBY (score 45) - same postal area, different streets
- "123 Main St, Boston MA" vs "456 Oak Ave, Boston MA" = DIFFERENT_BUT_NEARBY (score 35) - same city, different streets
- "123 Main St, Boston MA" vs "123 Main St, Seattle WA" = NO_MATCH (score 5) - different states"""

# Batch address comparison prompt for multiple address pairs
BATCH_ADDRESS_COMPARISON_PROMPT = """You are an expert address comparison system with comprehensive geographical knowledge and standardization capabilities.

STEP 1: STANDARDIZE ALL ADDRESSES FIRST
Apply geographical intelligence to each address:
- Expand abbreviations, fix misspellings
- Use postal code intelligence to identify correct cities/regions
- Apply geographical hierarchy: suburb/town → city → district/county → state/province → country
- Expand state/province abbreviations to full names (QLD → Queensland, CA → California, NY → New York)
- Normalize street types (St → Street, Ave → Avenue, Rd → Road)
- Apply country-specific formatting and administrative divisions

STEP 2: COMPARE EACH ADDRESS PAIR
Return a raw JSON array only (no markdown, no code fences, no text).
Each element must be a JSON object with this schema:

{
  "pair_index": 0,
  "original_address_1": "",
  "original_address_2": "",
  "standardized_address_1": "",
  "standardized_address_2": "",
  "overall_score": 0,
  "match_level": "IDENTICAL",
  "likely_same_address": false,
  "confidence": "high",
  "component_analysis": {
    "street_match": {"score": 0, "note": ""},
    "city_match": {"score": 0, "note": ""},
    "state_match": {"score": 0, "note": ""},
    "postal_code_match": {"score": 0, "note": ""},
    "geographic_relationship": ""
  },
  "explanation": "",
  "recommendation": ""
}

EXPLANATION REQUIREMENTS (CRITICAL):
For the "explanation" field, provide detailed, descriptive analysis like these examples:
- "Both addresses have the same street name and number. The city is the same but the postal codes differ slightly. The addition of 'World Trade Center' in the second address is a minor variation. Overall, they are very likely the same location."
- "The addresses share the same street number and name, and are in the same city and state. However, one specifies 'Suite 100' while the other does not mention a suite. The postal codes are identical, indicating the same building."
- "These addresses have different street numbers on the same street name. Address 1 is at number 123 while Address 2 is at number 456. Both are in downtown Boston, making them nearby but distinct locations."
- "The addresses are in completely different countries - one in Switzerland and one in the United States. They share no common geographic elements and represent entirely different physical locations."

EXPLANATION INSTRUCTIONS:
1. Compare specific address components (street numbers, street names, cities, postal codes)
2. Explain what elements match and what differs
3. Note any building names, suite numbers, or additional identifiers
4. Describe the geographical relationship (same building, same street, same city, etc.)
5. Use natural, descriptive language that explains the reasoning behind the score
6. Be specific about differences (e.g., "postal codes differ by 10 units" vs "different postal codes")
7. Mention any standardization applied (abbreviations expanded, formatting changes)

COMPARISON RULES (STRICT):
1. DIFFERENT STREET NUMBERS = Different addresses (score 0-10)
2. DIFFERENT STREET NAMES = Different addresses (score 0-15) 
3. DIFFERENT CITIES = Different addresses (score 0-20)
4. DIFFERENT STATES/PROVINCES = Different addresses (score 0-25)
5. Only if ALL major components match should you consider IDENTICAL or VERY_LIKELY_SAME scores

SCORING GUIDELINES AND MATCH LEVELS:
- 95-100: IDENTICAL - only minor formatting differences (St vs Street, abbreviations)
- 85-94: VERY_LIKELY_SAME - same street/building, minor variations in suite/unit
- 70-84: POSSIBLY_RELATED - same geographical area, some uncertainty
- 50-69: POSSIBLY_RELATED - same general area/neighborhood/postal zone
- 30-49: DIFFERENT_BUT_NEARBY - same city/town, different streets/areas
- 10-29: NO_MATCH - different areas (same state/province, different cities)
- 0-9: NO_MATCH - completely different locations (different states/countries)

Process these address pairs:"""

# Enhanced batch processing prompt for multiple addresses with geographical intelligence
BATCH_ADDRESS_STANDARDIZATION_PROMPT = """You are an expert global address standardization system with comprehensive geographical knowledge.
Return a raw JSON array only (no markdown, no code fences, no text).
Each element must be a JSON object with this schema and include "input_index" and "original_address".

TASKS FOR EACH ADDRESS:
- Must Expand abbreviations, fix misspellings
- Extract components and validate using geographical hierarchy knowledge
- Apply country-specific formatting and administrative divisions
- Validate postal codes by country and map to correct cities/regions
- Understand geographical relationships: suburb/town → city → district/county → state/province → country
- Use postal code intelligence to identify correct cities and administrative divisions
- Normalize casing: Title Case for names; country-specific state/province codes; proper postal code formats

GEOGRAPHICAL HIERARCHY RULES:
1. Identify the correct administrative city for suburbs/towns using postal codes
2. Expand state/province abbreviations to full names (e.g., QLD → Queensland, CA → California, NSW → New South Wales)
3. Map postal codes to their primary serving cities/regions globally
4. Distinguish between suburbs/neighborhoods and main cities
5. Apply country-specific administrative division structures
6. For ambiguous locations, prioritize based on postal code geographical mapping

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
1) Output only a valid JSON array of objects (no extra text).
2) Preserve input order using input_index (0-based).
3) Include original_address verbatim per item.
4) Apply country-specific formatting; prefer provided target country; otherwise auto-detect.
5) Never fabricate postal codes; use null and add "postal_code_missing".
6) Standardize abbreviations (St→Street, Ave→Avenue, Rd→Road, similarly for blocks and pockets etc.).
7) Set confidence to high | medium | low | unknown, and list issues precisely.
8) GEOGRAPHICAL INTELLIGENCE: Use postal code to identify correct city (e.g., 4818 → Townsville, QLD → Queensland).
9) HIERARCHY MAPPING: Place suburbs in "suburb" field, main administrative city in "city" field.
10) STATE EXPANSION: Always expand state/province abbreviations to full names globally.
11) MANDATORY COMPONENT EXTRACTION: Always attempt to populate ALL geographic components (district, region, suburb, locality, country, county, canton, prefecture, oblast) using postal code, city, and address knowledge. Only set to null if truly not applicable to that country's system.
12) ENHANCED GEOGRAPHICAL INFERENCE: Use your comprehensive knowledge of global postal systems, administrative divisions, and geographical hierarchies to infer and populate as many address components as possible. For UK addresses with OX postcodes, include district/suburb info when available.
13) POSTAL CODE INTELLIGENCE: Leverage postal code patterns to determine districts, regions, suburbs, and localities (e.g., OX2 → Jericho/Wolvercote area in Oxford, 10001 → Manhattan/NYC, 75001 → 1st arrondissement Paris).
14) ADMINISTRATIVE DIVISION MAPPING: Always include applicable administrative divisions for each country (counties for UK/US, prefectures for Japan, länder for Germany, regions for France, etc.).

EXAMPLES OF GEOGRAPHICAL HIERARCHY:
- "Mount St John QLD 4818" → suburb: "Mount St John", city: "Townsville", state: "Queensland", postal_code: "4818"
- "Brooklyn NY 11201" → suburb: "Brooklyn", city: "New York", state: "New York", postal_code: "11201"
- "Shibuya Tokyo 150-0002" → district: "Shibuya", city: "Tokyo", prefecture: "Tokyo", postal_code: "150-0002"
- "Southwark London SE1 9RT" → district: "Southwark", city: "London", postal_code: "SE1 9RT"
- "76 Great Clarendon Street, Oxford, OX2 6AU" → suburb: "Jericho", city: "Oxford", county: "Oxfordshire", region: "South East England", postal_code: "OX2 6AU"

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
    "batch_size": 10,  # Stable batch size: 10 addresses per batch (each needs ~250 tokens = 2500 total + 500 buffer = 3000 tokens)
    "max_batch_size": 10,  # Maximum safe batch size before hitting token limits
    "enable_batch_processing": True,
    "enable_batch_comparison": True  # Enable true batch comparison
}
