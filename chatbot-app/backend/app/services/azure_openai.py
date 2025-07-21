import requests
import json
import os
from dotenv import load_dotenv

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
        "temperature": 0.7,
        "max_tokens": 800,
        "frequency_penalty": 0,
        "presence_penalty": 0
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
    Returns a comprehensive system prompt for address standardization
    """
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
    """
    if prompt_type == "address_standardization":
        return get_address_standardization_prompt()
    else:
        return (
            "You are a helpful AI assistant. Please provide clear, informative, and helpful responses to user questions. "
            "Be conversational and engaging while providing accurate information."
        )

def standardize_address(raw_address: str):
    """
    Convenience function specifically for address standardization
    
    Args:
        raw_address (str): The raw address string to standardize
        
    Returns:
        dict: Standardized address in JSON format
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Call OpenAI with address standardization prompt
        response = connect_wso2(
            access_token=access_token,
            user_content=raw_address,
            prompt_type="address_standardization"
        )
        
        # Extract the content from OpenAI response
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            # Try to parse as JSON
            try:
                import json
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "Failed to parse response as JSON", "raw_response": content}
        else:
            return {"error": "No response received from OpenAI"}
            
    except Exception as e:
        return {"error": str(e)}

def standardize_multiple_addresses(address_list: list):
    """
    Standardize multiple addresses in batch
    
    Args:
        address_list (list): List of raw address strings
        
    Returns:
        list: List of standardized addresses
    """
    standardized_addresses = []
    
    for address in address_list:
        result = standardize_address(address)
        standardized_addresses.append(result)
    
    return standardized_addresses