import requests
import json
import os
from dotenv import load_dotenv

# Import address configuration
try:
    from app.config.address_config import (
        ADDRESS_STANDARDIZATION_PROMPT, 
        BATCH_ADDRESS_STANDARDIZATION_PROMPT,
        ORGANIZATION_SPECIFIC_PROMPT, 
        PROMPT_CONFIG,
        COUNTRY_FORMATS,
        get_country_specific_prompt
    )
    CONFIG_AVAILABLE = True
    print("✅ Address configuration loaded successfully")
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️  Warning: address_config.py not found, using fallback prompts")

# Load environment variables
load_dotenv()

def get_access_token():
    client_id = os.getenv("CLIENT_ID", "Client_ID")
    client_secret = os.getenv("CLIENT_SECRET", "Client_secret")
    auth_token_endpoint = os.getenv("WSO2_AUTH_URL", "https://api-test.cbre.com:443/token")

    print(f"Using client_id: {client_id}")
    print(f"Using client_secret: {client_secret[:4]}...")  # Don't print full secret in logs
    print(f"Auth endpoint: {auth_token_endpoint}")

    response = requests.post(auth_token_endpoint, data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    })

    print(f"Token response status: {response.status_code}")
    print(f"Token response body: {response.text}")

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to obtain access token: {response.text}')

def connect_wso2(access_token, user_content: str, system_prompt: str = None, prompt_type: str = "general"):
    deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "AOAIsharednonprodgpt35turbo16k")
    api_version = '2024-02-15-preview'
    proxy_url = 'https://api-test.cbre.com:443/t/digitaltech_us_edp/cbreopenaiendpoint/1/openai/deployments/{deployment_id}/chat/completions'
    url_variable = proxy_url.format(deployment_id=deployment_id)
    url_with_param = f'{url_variable}?api-version={api_version}'

    print(f"OpenAI URL: {url_with_param}")

    if not system_prompt:
        system_prompt = get_custom_system_prompt(prompt_type)

    # Get prompt configuration from config file
    config = get_prompt_config()

    request_body = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 800),
        "frequency_penalty": config.get("frequency_penalty", 0),
        "presence_penalty": config.get("presence_penalty", 0)
    }

    print(f"Request body: {json.dumps(request_body)}")

    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}

    response = requests.post(url_with_param, headers=headers, data=json.dumps(request_body))
    print(f"OpenAI response status: {response.status_code}")
    print(f"OpenAI response body: {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"OpenAI API error: {response.status_code} {response.text}")

def get_address_standardization_prompt():
    """
    Returns the address standardization prompt from configuration file
    Falls back to hardcoded prompt if config is not available
    """
    if CONFIG_AVAILABLE and PROMPT_CONFIG.get("use_address_standardization_prompt", True):
        return ADDRESS_STANDARDIZATION_PROMPT
    else:
        # Fallback hardcoded prompt (only used if config file is missing)
        return """You are an expert address standardization system. Your task is to take raw, unstructured address data and convert it into a standardized format following these guidelines:

**STANDARDIZATION RULES:**

1. **Format Structure**: Return addresses in this exact JSON format:
   ```json
   {
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
   }
   ```

2. **Street Types**: Standardize to full forms (Street, Avenue, Boulevard, Road, Drive, Lane, Court, Place, Way, Circle, etc.)

3. **Directionals**: Use standard abbreviations (N, S, E, W, NE, NW, SE, SW)

4. **Unit Types**: Standardize to (Apt, Suite, Unit, Floor, Room, Bldg, etc.)

5. **State/Province**: Use official 2-letter codes (NY, CA, TX, ON, BC, etc.)

6. **Country**: Use 3-letter ISO codes when possible (USA, CAN, GBR, etc.)

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

def get_custom_system_prompt(prompt_type="general"):
    """
    Returns different system prompts based on the use case
    Uses configuration file when available
    """
    if prompt_type == "address_standardization":
        return get_address_standardization_prompt()
    elif prompt_type == "batch_address_standardization" and CONFIG_AVAILABLE:
        return BATCH_ADDRESS_STANDARDIZATION_PROMPT
    elif prompt_type == "organization_specific" and CONFIG_AVAILABLE:
        return ORGANIZATION_SPECIFIC_PROMPT
    elif prompt_type == "batch_address_standardization":
        # Fallback batch prompt if config not available
        return """You are an expert address standardization system. Process multiple addresses and return them as a JSON array.

Return a JSON array where each object represents one standardized address with input_index for matching:

```json
[
  {
    "input_index": 0,
    "street_number": "123",
    "street_name": "Main Street",
    "street_type": "Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "formatted_address": "123 Main Street, New York, NY 10001, USA",
    "confidence": "high",
    "issues": []
  }
]
```

Rules:
1. Return ONLY valid JSON array
2. Use input_index (0-based) to match results to input addresses
3. Standardize abbreviations and correct spelling errors
4. Set appropriate confidence levels (high/medium/low)

Process these numbered addresses:"""
    else:
        return (
            "You are a helpful AI assistant. Please provide clear, informative, and helpful responses to user questions. "
            "Be conversational and engaging while providing accurate information."
        )

def get_prompt_config():
    """
    Get prompt configuration from config file
    """
    if CONFIG_AVAILABLE:
        return PROMPT_CONFIG
    else:
        return {
            "temperature": 0.7,
            "max_tokens": 800,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

def standardize_address(raw_address: str, target_country: str = None):
    """
    Convenience function specifically for address standardization with optional country-specific formatting
    
    Args:
        raw_address (str): The raw address string to standardize
        target_country (str, optional): Target country for country-specific formatting
        
    Returns:
        dict: Standardized address in JSON format
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Create enhanced user content with country context if provided
        if target_country and CONFIG_AVAILABLE:
            country_instruction = get_country_specific_prompt(target_country)
            enhanced_content = f"{country_instruction}\n\nAddress to standardize: {raw_address}"
        else:
            enhanced_content = raw_address
        
        # Call OpenAI with address standardization prompt
        response = connect_wso2(
            access_token=access_token,
            user_content=enhanced_content,
            prompt_type="address_standardization"
        )
        
        # Extract the content from OpenAI response
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            
            # Clean the content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ``` (in case it's just ```)
            if content.endswith('```'):
                content = content[:-3]  # Remove closing ```
            content = content.strip()
            
            # Try to parse as JSON
            try:
                import json
                result = json.loads(content)
                
                # If target country was specified, ensure country_code is set
                if target_country and 'country_code' not in result:
                    result['country_code'] = target_country.upper()
                
                # Apply country-specific formatting if available
                if target_country and target_country.upper() in COUNTRY_FORMATS and CONFIG_AVAILABLE:
                    format_pattern = COUNTRY_FORMATS[target_country.upper()]['format']
                    try:
                        # Create formatted address using country-specific pattern
                        formatted_parts = {}
                        for key, value in result.items():
                            if value and value != 'null':
                                formatted_parts[key] = str(value)
                            else:
                                formatted_parts[key] = ''
                        
                        # Apply the format pattern
                        country_formatted = format_pattern.format(**formatted_parts)
                        # Clean up empty fields and extra commas/spaces
                        country_formatted = ', '.join(filter(None, [part.strip() for part in country_formatted.replace(', ,', ',').split(', ') if part.strip()]))
                        result['formatted_address'] = country_formatted
                        
                    except (KeyError, ValueError) as e:
                        # If formatting fails, keep the original formatted_address
                        pass
                
                return result
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse response as JSON: {str(e)}", "raw_response": content}
        else:
            return {"error": "No response received from OpenAI"}
            
    except Exception as e:
        return {"error": str(e)}

def standardize_multiple_addresses(address_list: list, target_country: str = None, use_batch: bool = True):
    """
    Standardize multiple addresses efficiently using batch processing
    
    Args:
        address_list (list): List of raw address strings
        target_country (str, optional): Target country for country-specific formatting
        use_batch (bool): Whether to use batch processing (True) or individual calls (False)
        
    Returns:
        list: List of standardized addresses with input_index for matching
    """
    if not address_list:
        return []
    
    # Get batch size from config
    batch_size = PROMPT_CONFIG.get("batch_size", 10) if CONFIG_AVAILABLE else 10
    enable_batch = PROMPT_CONFIG.get("enable_batch_processing", True) if CONFIG_AVAILABLE else True
    
    # If batch processing is disabled or not requested, fall back to individual processing
    if not use_batch or not enable_batch:
        print(f"🔄 Processing {len(address_list)} addresses individually...")
        standardized_addresses = []
        for i, address in enumerate(address_list):
            result = standardize_address(address, target_country)
            result['input_index'] = i  # Add index for matching
            standardized_addresses.append(result)
        return standardized_addresses
    
    print(f"🚀 Batch processing {len(address_list)} addresses (batch size: {batch_size})...")
    all_results = []
    
    # Process addresses in batches
    for batch_start in range(0, len(address_list), batch_size):
        batch_end = min(batch_start + batch_size, len(address_list))
        batch_addresses = address_list[batch_start:batch_end]
        
        print(f"   Processing batch {batch_start//batch_size + 1}: addresses {batch_start+1}-{batch_end}")
        
        try:
            # Process this batch
            batch_results = _process_address_batch(batch_addresses, target_country, batch_start)
            all_results.extend(batch_results)
            
        except Exception as e:
            print(f"   ❌ Batch failed, falling back to individual processing: {str(e)}")
            # Fallback to individual processing for this batch
            for i, address in enumerate(batch_addresses):
                try:
                    result = standardize_address(address, target_country)
                    result['input_index'] = batch_start + i
                    all_results.append(result)
                except Exception as individual_error:
                    # Create error result
                    error_result = {
                        'input_index': batch_start + i,
                        'error': str(individual_error),
                        'original_address': address,
                        'formatted_address': '',
                        'confidence': 'low',
                        'issues': ['processing_error']
                    }
                    all_results.append(error_result)
    
    print(f"✅ Batch processing completed: {len(all_results)} addresses processed")
    return all_results

def _process_address_batch(address_list: list, target_country: str = None, batch_offset: int = 0):
    """
    Process a batch of addresses in a single API call
    
    Args:
        address_list (list): List of addresses in this batch
        target_country (str, optional): Target country for formatting
        batch_offset (int): Offset for input_index calculation
        
    Returns:
        list: List of standardized addresses
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Prepare batch content
        numbered_addresses = []
        for i, address in enumerate(address_list):
            numbered_addresses.append(f"{i}: {address}")
        
        batch_content = "\n".join(numbered_addresses)
        
        # Add country context if provided
        if target_country and CONFIG_AVAILABLE:
            country_instruction = get_country_specific_prompt(target_country)
            enhanced_content = f"{country_instruction}\n\nAddresses to standardize:\n{batch_content}"
        else:
            enhanced_content = batch_content
        
        # Get batch prompt
        if CONFIG_AVAILABLE:
            system_prompt = BATCH_ADDRESS_STANDARDIZATION_PROMPT
        else:
            system_prompt = get_custom_system_prompt("batch_address_standardization")
        
        # Call OpenAI with batch prompt
        response = connect_wso2(
            access_token=access_token,
            user_content=enhanced_content,
            system_prompt=system_prompt
        )
        
        # Extract and parse the batch response
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            
            # Clean the content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse as JSON array
            try:
                import json
                batch_results = json.loads(content)
                
                # Ensure it's a list
                if not isinstance(batch_results, list):
                    raise ValueError("Expected JSON array from batch processing")
                
                # Adjust input_index with batch_offset and add missing fields
                processed_results = []
                for result in batch_results:
                    if isinstance(result, dict):
                        # Adjust the input_index with batch offset
                        original_index = result.get('input_index', 0)
                        result['input_index'] = batch_offset + original_index
                        
                        # Add original address for reference
                        if original_index < len(address_list):
                            result['original_address'] = address_list[original_index]
                        
                        # Apply country-specific formatting if needed
                        if target_country and target_country.upper() in COUNTRY_FORMATS and CONFIG_AVAILABLE:
                            _apply_country_formatting(result, target_country)
                        
                        processed_results.append(result)
                
                return processed_results
                
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse batch response as JSON: {str(e)}")
        else:
            raise ValueError("No response received from OpenAI for batch")
            
    except Exception as e:
        raise Exception(f"Batch processing failed: {str(e)}")

def _apply_country_formatting(result: dict, target_country: str):
    """Apply country-specific formatting to a result"""
    try:
        format_pattern = COUNTRY_FORMATS[target_country.upper()]['format']
        formatted_parts = {}
        for key, value in result.items():
            if value and value != 'null':
                formatted_parts[key] = str(value)
            else:
                formatted_parts[key] = ''
        
        # Apply the format pattern
        country_formatted = format_pattern.format(**formatted_parts)
        # Clean up empty fields and extra commas/spaces
        country_formatted = ', '.join(filter(None, [part.strip() for part in country_formatted.replace(', ,', ',').split(', ') if part.strip()]))
        result['formatted_address'] = country_formatted
        
    except (KeyError, ValueError):
        # If formatting fails, keep the original formatted_address
        pass