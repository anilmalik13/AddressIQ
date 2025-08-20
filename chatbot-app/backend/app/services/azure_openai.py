import requests
import json
import os
import chardet
import pandas as pd
from dotenv import load_dotenv

# Import address configuration
try:
    from app.config.address_config import (
        ADDRESS_STANDARDIZATION_PROMPT, 
        BATCH_ADDRESS_STANDARDIZATION_PROMPT,
        ORGANIZATION_SPECIFIC_PROMPT,
        ADDRESS_COMPARISON_PROMPT,
        PROMPT_CONFIG,
        COUNTRY_FORMATS,
        get_country_specific_prompt
    )
    CONFIG_AVAILABLE = True
    # Avoid non-ASCII emoji in import-time logs to prevent encoding issues on some consoles
    print("Address configuration loaded successfully")
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: address_config.py not found, using fallback prompts")

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

    # Ensure Unicode-safe content
    user_content = ensure_unicode_safe_content(user_content)
    system_prompt = ensure_unicode_safe_content(system_prompt)

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

    print(f"Request body: {json.dumps(request_body, ensure_ascii=False)}")

    headers = {
        'Content-Type': 'application/json; charset=utf-8', 
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post(
        url_with_param, 
        headers=headers, 
        data=json.dumps(request_body, ensure_ascii=False).encode('utf-8')
    )
    print(f"OpenAI response status: {response.status_code}")
    print(f"OpenAI response body: {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"OpenAI API error: {response.status_code} {response.text}")

def get_address_standardization_prompt():
    """
    Returns the address standardization prompt from configuration file
    Falls back to simple prompt if config is not available
    """
    if CONFIG_AVAILABLE and PROMPT_CONFIG.get("use_address_standardization_prompt", True):
        return ADDRESS_STANDARDIZATION_PROMPT
    else:
        # Simple fallback if config file is missing
        return "You are an address standardization system. Standardize the given address and return it in JSON format with fields: street_number, street_name, city, state, postal_code, country, formatted_address, confidence."

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
    elif prompt_type == "comparison" and CONFIG_AVAILABLE:
        return ADDRESS_COMPARISON_PROMPT
    elif prompt_type == "batch_address_standardization":
        # Minimal fallback if config not available
        return "You are an address standardization system. Process multiple addresses and return them as a JSON array with input_index for matching."
    else:
        return "You are a helpful AI assistant. Please provide clear, informative, and helpful responses."

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

def read_csv_with_encoding_detection(file_path: str):
    """
    Read CSV file with automatic encoding detection to handle international characters
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: DataFrame with properly decoded content
        
    Raises:
        Exception: If file cannot be read with any encoding
    """
    print(f"📄 Reading CSV file: {file_path}")
    
    # First, detect the encoding
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result['encoding']
            confidence = encoding_result['confidence']
        
        print(f"🔍 Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
    except Exception as e:
        print(f"⚠️ Warning: Could not detect encoding: {str(e)}")
        detected_encoding = None
        confidence = 0
    
    # List of encodings to try, prioritizing detected encoding
    encodings_to_try = []
    
    # Add detected encoding first if confidence is reasonable
    if detected_encoding and confidence > 0.7:
        encodings_to_try.append(detected_encoding)
    
    # Add common encodings for international content
    common_encodings = [
        'utf-8',           # Standard Unicode
        'utf-8-sig',       # UTF-8 with BOM (Excel exports)
        'cp1252',          # Windows Western European
        'iso-8859-1',      # Latin-1 (Western European)
        'windows-1252',    # Windows encoding
        'latin1',          # Latin-1 fallback
        'cp1251',          # Windows Cyrillic
        'iso-8859-2',      # Central European
        'iso-8859-15',     # Western European with Euro
        'gb2312',          # Chinese Simplified
        'big5',            # Chinese Traditional
        'shift_jis',       # Japanese
        'euc-kr',          # Korean
        'windows-1256',    # Arabic
        'windows-1255',    # Hebrew
    ]
    
    # Add detected encoding again if not already added
    if detected_encoding and detected_encoding not in encodings_to_try:
        encodings_to_try.append(detected_encoding)
    
    # Add common encodings
    for encoding in common_encodings:
        if encoding not in encodings_to_try:
            encodings_to_try.append(encoding)
    
    # Try each encoding
    for encoding in encodings_to_try:
        if encoding is None:
            continue
        try:
            print(f"🔄 Trying encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"✅ Successfully read file with {encoding} encoding")
            print(f"📊 Loaded {len(df)} rows with {len(df.columns)} columns")
            return df
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"❌ Failed with {encoding}: {str(e)}")
            continue
        except Exception as e:
            print(f"❌ Error with {encoding}: {str(e)}")
            continue
    
    # Last resort: read with errors='ignore' to handle any remaining issues
    try:
        print("🆘 Last resort: Reading with UTF-8 and replacing invalid characters")
        # Open file with error handling first, then pass to pandas
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            df = pd.read_csv(f)
        print(f"⚠️ Read file with UTF-8 and replaced invalid characters")
        print(f"📊 Loaded {len(df)} rows with {len(df.columns)} columns")
        return df
    except Exception as e:
        raise Exception(f"❌ Could not read CSV file with any encoding: {str(e)}")

def ensure_unicode_safe_content(content: str) -> str:
    """
    Ensure content is Unicode-safe for API transmission
    
    Args:
        content (str): Input content that may contain international characters
        
    Returns:
        str: Unicode-safe content
    """
    if not isinstance(content, str):
        content = str(content)
    
    try:
        # Normalize Unicode characters to ensure consistency
        import unicodedata
        content = unicodedata.normalize('NFC', content)
    except ImportError:
        # unicodedata should be available in standard library, but just in case
        pass
    
    # Ensure it's properly encoded as UTF-8 string
    try:
        content.encode('utf-8')
        return content
    except UnicodeEncodeError as e:
        print(f"⚠️ Warning: Unicode encoding issue fixed: {str(e)}")
        # Replace problematic characters with safe alternatives
        return content.encode('utf-8', errors='replace').decode('utf-8')

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
        # Ensure Unicode-safe input
        raw_address = ensure_unicode_safe_content(raw_address)
        
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
        
        # Prepare batch content with Unicode-safe processing
        numbered_addresses = []
        for i, address in enumerate(address_list):
            # Ensure each address is Unicode-safe
            safe_address = ensure_unicode_safe_content(str(address))
            numbered_addresses.append(f"{i}: {safe_address}")
        
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
                            result['original_address'] = ensure_unicode_safe_content(str(address_list[original_index]))
                        
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

def compare_addresses(comparison_prompt: str, target_country: str = None):
    """
    Compare two addresses using OpenAI with a specific comparison prompt
    
    Args:
        comparison_prompt (str): The full comparison prompt with addresses and instructions
        target_country (str, optional): Target country for context
        
    Returns:
        dict: Comparison result in JSON format
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Create comparison system prompt
        comparison_system_prompt = """You are an expert address comparison system. 
Analyze the two addresses provided and return a detailed comparison in JSON format.
Return only valid JSON with no markdown formatting or code blocks."""
        
        # Call OpenAI with comparison-specific settings
        response = connect_wso2(
            access_token=access_token,
            user_content=comparison_prompt,
            system_prompt=comparison_system_prompt,
            prompt_type="comparison"
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
                return result
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse response as JSON: {str(e)}", "raw_response": content}
        else:
            return {"error": "No response received from OpenAI"}
            
    except Exception as e:
        return {"error": str(e)}

def compare_multiple_addresses(address_pairs: list, batch_size: int = 5):
    """
    Compare multiple address pairs efficiently using batch processing with standardization
    
    Args:
        address_pairs (list): List of tuples/dicts containing address pairs to compare
                             Format: [{'address1': 'addr1', 'address2': 'addr2'}, ...]
                             Or: [('addr1', 'addr2'), ...]
        batch_size (int): Number of address pairs to process in one batch
        
    Returns:
        list: List of comparison results with batch_index and standardized addresses
    """
    if not address_pairs:
        return []
    
    print(f"🚀 Batch comparing {len(address_pairs)} address pairs (batch size: {batch_size})...")
    all_results = []
    
    # Process address pairs in batches
    for batch_start in range(0, len(address_pairs), batch_size):
        batch_end = min(batch_start + batch_size, len(address_pairs))
        batch_pairs = address_pairs[batch_start:batch_end]
        
        print(f"   Processing batch {batch_start//batch_size + 1}: pairs {batch_start + 1}-{batch_end}")
        
        try:
            # Process this batch
            batch_results = _process_comparison_batch_with_standardization(batch_pairs, batch_start)
            all_results.extend(batch_results)
            
        except Exception as e:
            print(f"   ❌ Batch failed, falling back to individual processing: {str(e)}")
            # Fallback to individual processing for this batch
            for i, pair in enumerate(batch_pairs):
                try:
                    # Extract addresses from pair
                    if isinstance(pair, dict):
                        addr1, addr2 = pair.get('address1', ''), pair.get('address2', '')
                    else:
                        addr1, addr2 = pair[0], pair[1]
                    
                    # Standardize both addresses individually
                    std_result1 = standardize_address(addr1)
                    std_result2 = standardize_address(addr2)
                    
                    # Create comparison prompt for individual processing
                    comparison_prompt = _create_single_comparison_prompt(addr1, addr2)
                    result = compare_addresses(comparison_prompt)
                    result['batch_index'] = batch_start + i
                    result['original_address_1'] = addr1
                    result['original_address_2'] = addr2
                    result['standardized_address_1'] = std_result1.get('formatted_address', '')
                    result['standardized_address_2'] = std_result2.get('formatted_address', '')
                    all_results.append(result)
                    
                except Exception as individual_error:
                    # Create error result
                    error_result = {
                        'batch_index': batch_start + i,
                        'error': str(individual_error),
                        'original_address_1': addr1 if 'addr1' in locals() else '',
                        'original_address_2': addr2 if 'addr2' in locals() else '',
                        'standardized_address_1': '',
                        'standardized_address_2': '',
                        'match_level': 'ERROR',
                        'confidence_score': 0,
                        'analysis': f'Processing error: {str(individual_error)}',
                        'method_used': 'error_fallback'
                    }
                    all_results.append(error_result)
    
    print(f"✅ Batch comparison completed: {len(all_results)} pairs processed")
    return all_results

def _process_comparison_batch_with_standardization(address_pairs: list, batch_offset: int = 0):
    """
    Process a batch of address pairs with both comparison and standardization in a single API call
    
    Args:
        address_pairs (list): List of address pairs in this batch
        batch_offset (int): Offset for batch_index calculation
        
    Returns:
        list: List of comparison results with standardized addresses
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Create enhanced batch comparison prompt that includes standardization
        batch_comparison_prompt = _create_batch_comparison_and_standardization_prompt(address_pairs, batch_offset)
        
        # Create enhanced system prompt for batch comparison and standardization
        batch_system_prompt = """You are an expert address comparison and standardization system for batch processing.
For each address pair, first standardize both addresses, then compare them and return a JSON array with detailed results.
Return only valid JSON array with no markdown formatting or code blocks.

Each result must include:
- batch_index: The index of the pair in the batch
- original_address_1: First address as provided
- original_address_2: Second address as provided
- standardized_address_1: Standardized version of first address
- standardized_address_2: Standardized version of second address
- overall_score: Similarity score (0-100)
- match_level: EXACT, HIGH, MEDIUM, LOW, or NO_MATCH
- likely_same_address: boolean
- confidence: high, medium, or low
- analysis: Detailed explanation of the comparison

CRITICAL: Return a JSON array with one object per address pair comparison and standardization."""
        
        # Call OpenAI with batch comparison and standardization prompt
        response = connect_wso2(
            access_token=access_token,
            user_content=batch_comparison_prompt,
            system_prompt=batch_system_prompt,
            prompt_type="comparison"
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
                    # If it's a single object, wrap it in a list
                    if isinstance(batch_results, dict):
                        batch_results = [batch_results]
                    else:
                        raise ValueError("Expected JSON array from batch comparison and standardization")
                
                # Adjust batch_index with batch_offset and ensure required fields
                processed_results = []
                for i, result in enumerate(batch_results):
                    if isinstance(result, dict):
                        # Ensure batch_index is correctly set
                        result['batch_index'] = batch_offset + i
                        
                        # Add original addresses if not present
                        if i < len(address_pairs):
                            pair = address_pairs[i]
                            if isinstance(pair, dict):
                                if 'original_address_1' not in result:
                                    result['original_address_1'] = pair.get('address1', '')
                                if 'original_address_2' not in result:
                                    result['original_address_2'] = pair.get('address2', '')
                            else:
                                if 'original_address_1' not in result:
                                    result['original_address_1'] = pair[0]
                                if 'original_address_2' not in result:
                                    result['original_address_2'] = pair[1]
                        
                        # Ensure required fields exist
                        if 'match_level' not in result:
                            result['match_level'] = 'UNKNOWN'
                        if 'confidence_score' not in result:
                            result['confidence_score'] = result.get('overall_score', 0)
                        if 'analysis' not in result:
                            result['analysis'] = 'Batch comparison and standardization completed'
                        if 'method_used' not in result:
                            result['method_used'] = 'azure_openai_batch_with_standardization'
                        if 'standardized_address_1' not in result:
                            result['standardized_address_1'] = ''
                        if 'standardized_address_2' not in result:
                            result['standardized_address_2'] = ''
                        
                        processed_results.append(result)
                
                return processed_results
                
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse batch comparison and standardization response as JSON: {str(e)}")
        else:
            raise ValueError("No response received from OpenAI for batch comparison and standardization")
            
    except Exception as e:
        raise Exception(f"Batch comparison and standardization processing failed: {str(e)}")

def _create_batch_comparison_and_standardization_prompt(address_pairs: list, batch_offset: int = 0):
    """
    Create a batch prompt for both comparison and standardization of multiple address pairs
    
    Args:
        address_pairs (list): List of address pairs
        batch_offset (int): Starting index for batch numbering
        
    Returns:
        str: Formatted batch comparison and standardization prompt
    """
    prompt_parts = []
    prompt_parts.append("For each address pair below, first STANDARDIZE both addresses, then COMPARE them:")
    prompt_parts.append("")
    
    for i, pair in enumerate(address_pairs):
        batch_index = batch_offset + i
        
        if isinstance(pair, dict):
            addr1 = ensure_unicode_safe_content(str(pair.get('address1', '')))
            addr2 = ensure_unicode_safe_content(str(pair.get('address2', '')))
        else:
            addr1 = ensure_unicode_safe_content(str(pair[0]))
            addr2 = ensure_unicode_safe_content(str(pair[1]))
        
        prompt_parts.append(f"PAIR {batch_index}:")
        prompt_parts.append(f"Address 1: \"{addr1}\"")
        prompt_parts.append(f"Address 2: \"{addr2}\"")
        prompt_parts.append("")
    
    # Add standardization and comparison instructions
    prompt_parts.append("TASK INSTRUCTIONS:")
    prompt_parts.append("1. STANDARDIZE each address into proper format (street number, street name, city, state, postal code)")
    prompt_parts.append("2. COMPARE the standardized addresses using the rules below")
    prompt_parts.append("")
    
    if CONFIG_AVAILABLE:
        # Use the configured comparison prompt guidelines
        prompt_parts.append("COMPARISON RULES:")
        prompt_parts.append("1. DIFFERENT STREET NUMBERS = Different addresses (score 0-10)")
        prompt_parts.append("2. DIFFERENT STREET NAMES = Different addresses (score 0-15)")
        prompt_parts.append("3. DIFFERENT CITIES = Different addresses (score 0-20)")
        prompt_parts.append("4. DIFFERENT STATES/PROVINCES = Different addresses (score 0-25)")
        prompt_parts.append("5. Only if ALL major components match should you consider HIGH scores")
        prompt_parts.append("")
        prompt_parts.append("SCORING GUIDELINES:")
        prompt_parts.append("- 95-100: Identical location (only minor formatting like St vs Street)")
        prompt_parts.append("- 85-94: Very likely same location (same street/building, minor variations)")
        prompt_parts.append("- 70-84: Probably same location (some uncertainty in components)")
        prompt_parts.append("- 50-69: Possibly related (same general area/neighborhood)")
        prompt_parts.append("- 30-49: Different but nearby (same city/town)")
        prompt_parts.append("- 0-29: Completely different locations")
    
    prompt_parts.append("")
    prompt_parts.append("Return a JSON array with one object per address pair containing both standardization and comparison results.")
    
    return "\n".join(prompt_parts)

def _create_single_comparison_prompt(address1: str, address2: str):
    """
    Create a comparison prompt for a single address pair (fallback)
    
    Args:
        address1 (str): First address
        address2 (str): Second address
        
    Returns:
        str: Formatted comparison prompt
    """
    if CONFIG_AVAILABLE:
        return ADDRESS_COMPARISON_PROMPT.format(
            address1=address1,
            address2=address2
        )
    else:
        return f"""Compare these two addresses:
Address 1: "{address1}"
Address 2: "{address2}"

Provide a detailed comparison including match level, confidence score, and analysis."""