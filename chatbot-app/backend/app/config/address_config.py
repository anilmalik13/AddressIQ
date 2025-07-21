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

# Additional system prompt customizations for your organization
ORGANIZATION_SPECIFIC_PROMPT = """
**ORGANIZATION-SPECIFIC REQUIREMENTS:**
- Prioritize US address formats as primary standard
- Always include country code for international addresses  
- Flag any addresses that don't meet minimum confidence threshold
- Maintain consistency with corporate directory standards
- Handle corporate campus addresses with building codes
"""
