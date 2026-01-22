#!/usr/bin/env python3
"""
Address Splitter Module for AddressIQ
Splits addresses based on specific rules before standardization
Supports both rule-based and GPT-based splitting
"""

import re
import json
from typing import List, Dict, Any, Tuple, Optional

# Import Azure OpenAI for GPT-based splitting
try:
    from app.services.azure_openai import connect_wso2, get_access_token
    GPT_AVAILABLE = True
except ImportError:
    GPT_AVAILABLE = False
    print("⚠️  GPT-based splitting not available - Azure OpenAI module not found")


class AddressSplitter:
    """
    Analyzes addresses and splits them into multiple addresses when appropriate
    based on specific business rules or GPT analysis.
    """
    
    def __init__(self, use_gpt: bool = False):
        """
        Initialize the address splitter
        
        Args:
            use_gpt: Whether to use GPT-based splitting (default: False, uses rule-based)
        """
        self.use_gpt = use_gpt and GPT_AVAILABLE
        
        if self.use_gpt:
            print("🤖 AddressSplitter initialized with GPT-based analysis")
        else:
            if use_gpt and not GPT_AVAILABLE:
                print("⚠️  GPT requested but not available, falling back to rule-based")
            print("📋 AddressSplitter initialized with rule-based analysis")
        
        # Define patterns for "no split" conditions
        
        # Pattern 1: Range of street numbers (e.g., "123-456", "3C-5C", "211-245")
        self.range_pattern = re.compile(r'\b\d+[A-Z]?\s*-\s*\d+[A-Z]?\b', re.IGNORECASE)
        
        # Pattern 2: Fractional identifiers (Apt, Ste, Unit, #, etc.)
        self.fractional_identifiers = [
            r'\bApt\.?\s+', r'\bApartment\s+',
            r'\bSte\.?\s+', r'\bSuite\s+',
            r'\bUnit\.?\s+', r'\bUnits\s+',
            r'\b#\s*\d+',
            r'\bFloor\s+',
            r'\bBldg\.?\s+', r'\bBuilding\s+',
            r'\bLot\s+',
            r'\bSpace\s+',
            r'\bRoom\s+',
            r'\bRm\.?\s+'
        ]
        self.fractional_pattern = re.compile('|'.join(self.fractional_identifiers), re.IGNORECASE)
        
        # Pattern 3: Directional identifiers
        self.directional_identifiers = [
            r'\bNEQ\b', r'\bSWC\b', r'\bNEC\b', r'\bSEC\b', r'\bNWC\b',
            r'\beast of\b', r'\bwest of\b', r'\bnorth of\b', r'\bsouth of\b',
            r'\bE of\b', r'\bW of\b', r'\bN of\b', r'\bS of\b',
            r'\bE/S\b', r'\bW/L\b', r'\bN/S\b', r'\bS/S\b',
            r'\bbetween\b',
            r'\bintersection\b',
            r'\bTOWNSHIP\b', r'\bRANGE\b', r'\bSECTION\b',
            r'\bSE on\b', r'\bNE on\b', r'\bSW on\b', r'\bNW on\b',
            r'\bSE of\b', r'\bNE of\b', r'\bSW of\b', r'\bNW of\b'
        ]
        self.directional_pattern = re.compile('|'.join(self.directional_identifiers), re.IGNORECASE)
        
        # Pattern for detecting "and" or "&" that might indicate multiple addresses
        self.and_pattern = re.compile(r'\s+and\s+|\s*&\s*', re.IGNORECASE)
        
        # Pattern for detecting street numbers
        self.street_number_pattern = re.compile(r'\b\d+[A-Z]?\b')
    
    def should_not_split(self, address: str) -> Tuple[bool, str]:
        """
        Determines if an address should NOT be split based on the "no split" rules.
        
        Returns:
            Tuple[bool, str]: (should_not_split, reason)
        """
        
        # Rule 1: Contains a range of street numbers
        if self.range_pattern.search(address):
            return True, "Contains range of street numbers"
        
        # Rule 2: Contains fractional identifiers
        if self.fractional_pattern.search(address):
            return True, "Contains fractional identifiers (Apt, Ste, Unit, etc.)"
        
        # Rule 3: Contains directional identifiers
        if self.directional_pattern.search(address):
            return True, "Contains directional identifiers"
        
        # Rule 4: No street numbers
        street_numbers = self.street_number_pattern.findall(address)
        if not street_numbers:
            return True, "No street numbers found"
        
        return False, ""
    
    def detect_potential_split(self, address: str, address2: str = None) -> Tuple[bool, str]:
        """
        Detects if an address could potentially be split into multiple addresses.
        Only splits on coordinating conjunctions (and, &) - NOT on commas.
        
        Args:
            address: Primary address field
            address2: Secondary address field (optional)
        
        Returns:
            Tuple[bool, str]: (should_split, reason)
        """
        
        # First check if we should NOT split based on no-split rules
        should_not, reason = self.should_not_split(address)
        if should_not:
            return False, f"No split: {reason}"
        
        # Check for "and" or "&" in the address (coordinating conjunctions)
        has_and = self.and_pattern.search(address)
        
        # ONLY split if we have coordinating conjunctions (and, &)
        # Commas are NOT used as split delimiters - they're part of normal address formatting
        if not has_and:
            # Check if address2 contains separate addresses with coordinating conjunctions
            if address2 and address2.strip():
                if self.and_pattern.search(address2):
                    return True, "Address2 contains coordinating conjunctions"
            return False, "No coordinating conjunctions ('and' or '&') found"
        
        # Has "and" or "&" - this is a potential split
        # Check for special characters that would indicate it's NOT multiple addresses
        special_chars = ['(', ')', '[', ']', '{', '}', ':', ';']
        has_special = any(char in address for char in special_chars)
        
        if has_special:
            return False, "Contains special characters indicating single address context"
        
        return True, "Contains coordinating conjunctions ('and' or '&') - potential multiple addresses"
    
    def split_address(self, address: str, address2: str = None) -> List[str]:
        """
        Splits an address into multiple addresses based on the detection rules.
        
        Args:
            address: Primary address field
            address2: Secondary address field (optional)
        
        Returns:
            List[str]: List of individual addresses
        """
        
        # Check if we should split
        should_split, reason = self.detect_potential_split(address, address2)
        
        if not should_split:
            # Return original address as single item
            return [address]
        
        # Perform the split - ONLY split on coordinating conjunctions (and, &)
        # Commas are preserved as part of the address formatting
        addresses = self._split_and_addresses(address)
        
        # Handle address2 if present
        if address2 and address2.strip():
            address2_parts = re.split(r'\s+and\s+|\s*&\s*', address2, flags=re.IGNORECASE)
            addresses.extend([part.strip() for part in address2_parts if part.strip()])
        
        # Filter out empty addresses
        addresses = [addr for addr in addresses if addr]
        
        return addresses if addresses else [address]
    
    def _split_and_addresses(self, address: str) -> List[str]:
        """
        Splits addresses connected by "and" or "&", reconstructing complete addresses.
        Handles comma-separated numbers before coordinating conjunctions.
        
        Example: "10255 and 10261 Iron Rock Way"
        Should become: ["10255 Iron Rock Way", "10261 Iron Rock Way"]
        
        Example: "328 & 348 14th Street NW"
        Should become: ["328 14th Street NW", "348 14th Street NW"]
        
        Example: "10, 20, 30 and 40 Main Street"
        Should become: ["10 Main Street", "20 Main Street", "30 Main Street", "40 Main Street"]
        """
        
        # Split by "and" or "&"
        parts = re.split(r'\s+and\s+|\s*&\s*', address, flags=re.IGNORECASE)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) <= 1:
            return parts
        
        result_addresses = []
        
        # Find the part with the most content (likely has the full street name)
        base_street_name = None
        
        # Look for the rightmost part with substantial text (street name)
        for part in reversed(parts):
            # Check if this part has a street name (words, not just numbers)
            word_match = re.search(r'[A-Za-z]{3,}', part)
            if word_match:
                # Extract street name (everything after the first number)
                num_match = re.match(r'^(\d+)\s+(.+)', part)
                if num_match:
                    base_street_name = num_match.group(2).strip()
                    break
        
        # Reconstruct addresses
        if base_street_name:
            for part in parts:
                part = part.strip()
                
                # Check if this part contains comma-separated numbers
                # e.g., "10, 20, 30" before the coordinating conjunction
                if ',' in part:
                    # Split by commas and process each number
                    numbers = [n.strip() for n in part.split(',')]
                    for num in numbers:
                        if num and re.match(r'^\d+$', num):
                            # Standalone number - reconstruct with base street name
                            result_addresses.append(f"{num} {base_street_name}")
                        elif num:
                            # Has other content - use as-is
                            result_addresses.append(num)
                elif re.match(r'^\d+$', part):
                    # Standalone number (no commas) - reconstruct
                    result_addresses.append(f"{part} {base_street_name}")
                else:
                    # Already has content, use as-is
                    result_addresses.append(part)
        else:
            # No base street name found, return parts as-is
            result_addresses = parts
        
        return result_addresses
    
    def _split_comma_separated_addresses(self, address: str) -> List[str]:
        """
        Intelligently splits comma-separated addresses.
        
        Example: "10255 and 10261 Iron Rock Way"
        Should become: ["10255 Iron Rock Way", "10261 Iron Rock Way"]
        
        Example: "0, 19, 20, 97 & 105 Morrisville Plaza"
        Should become: ["0 Morrisville Plaza", "19 Morrisville Plaza", "20 Morrisville Plaza", 
                        "97 Morrisville Plaza", "105 Morrisville Plaza"]
        """
        
        # First split by "and" or "&"
        and_parts = re.split(r'\s+and\s+|\s*&\s*', address, flags=re.IGNORECASE)
        
        result_addresses = []
        
        for part in and_parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if this part has commas
            if ',' in part:
                segments = [s.strip() for s in part.split(',')]
                
                # Find the last segment that has a street name (words, not just numbers)
                # This is typically the "base" address with the full street name
                base_street_name = None
                
                # Look for the rightmost segment with substantial text (street name)
                for seg in reversed(segments):
                    # Check if segment has words (not just numbers/directions)
                    # Match patterns like "Iron Rock Way", "Morrisville Plaza", "14th Street NW"
                    word_match = re.search(r'[A-Za-z]{3,}', seg)
                    if word_match:
                        # Extract everything after the first number (if any)
                        num_match = re.match(r'^(\d+)\s+(.+)', seg)
                        if num_match:
                            base_street_name = num_match.group(2).strip()
                        else:
                            # No number, the whole thing might be the street name
                            base_street_name = seg.strip()
                        break
                
                # If we found a base street name
                if base_street_name:
                    for seg in segments:
                        seg = seg.strip()
                        if not seg:
                            continue
                        
                        # Check if this segment is ONLY a number (standalone number)
                        if re.match(r'^\d+$', seg):
                            # Reconstruct: number + street name
                            result_addresses.append(f"{seg} {base_street_name}")
                        else:
                            # Has more content - it's already a complete address
                            result_addresses.append(seg)
                else:
                    # No base street name found, treat each comma-separated part as separate
                    result_addresses.extend([s for s in segments if s])
            else:
                # No commas, add as-is
                result_addresses.append(part)
        
        return [addr for addr in result_addresses if addr]
    
    def analyze_and_split(self, address1: str, address2: str = None) -> Dict[str, Any]:
        """
        Analyzes an address and splits it if appropriate.
        Uses GPT-based analysis if enabled, otherwise uses rule-based logic.
        
        Args:
            address1: Primary address field
            address2: Secondary address field (optional)
        
        Returns:
            Dict containing:
                - original_address1: Original address1
                - original_address2: Original address2 (if provided)
                - should_split: Boolean indicating if split occurred
                - split_reason: Reason for split/no-split
                - addresses: List of split addresses
                - split_count: Number of addresses after split
                - method_used: 'gpt' or 'rule-based'
        """
        
        # Use GPT-based splitting if enabled
        if self.use_gpt:
            return self._gpt_based_split(address1, address2)
        else:
            return self._rule_based_split(address1, address2)
    
    def _rule_based_split(self, address1: str, address2: str = None) -> Dict[str, Any]:
        """
        Rule-based address splitting logic (original implementation)
        """
        # Combine address fields for analysis if both present
        combined = address1
        if address2 and address2.strip():
            combined = f"{address1} | {address2}"
        
        # Check split criteria
        should_split, reason = self.detect_potential_split(address1, address2)
        
        # Perform split if needed
        if should_split:
            addresses = self.split_address(address1, address2)
        else:
            addresses = [address1]
        
        return {
            'original_address1': address1,
            'original_address2': address2 if address2 else '',
            'should_split': should_split,
            'split_reason': reason,
            'addresses': addresses,
            'split_count': len(addresses),
            'method_used': 'rule-based'
        }
    
    def _gpt_based_split(self, address1: str, address2: str = None) -> Dict[str, Any]:
        """
        GPT-based address splitting using Azure OpenAI
        
        Args:
            address1: Primary address field
            address2: Secondary address field (optional)
            
        Returns:
            Dict with split analysis and results
        """
        
        if not GPT_AVAILABLE:
            print("⚠️  GPT not available, falling back to rule-based splitting")
            return self._rule_based_split(address1, address2)
        
        try:
            # Prepare the prompt for GPT
            prompt = self._create_gpt_split_prompt(address1, address2)
            
            # Get access token and call GPT
            access_token = get_access_token()
            
            system_prompt = """You are an expert address parser specializing in identifying when a single address field contains multiple distinct addresses that should be separated.

Your task is to analyze address fields and determine:
1. Whether the address contains multiple distinct addresses
2. If yes, split them into individual addresses
3. Provide reasoning for your decision

Follow these rules:
- DO NOT SPLIT if the address contains a range (e.g., "123-456 Main St")
- DO NOT SPLIT if it contains unit/apt/suite identifiers (e.g., "Units A, B, C")
- DO NOT SPLIT if it has directional descriptions (e.g., "NE of", "SW corner")
- DO NOT SPLIT if there are no street numbers (e.g., "Highway 40 and K")
- DO SPLIT if it contains "and" or "&" separating complete addresses
- DO SPLIT if it has comma-separated street numbers with a street name (e.g., "100, 200, 300 Main St")

Return a JSON object with:
- should_split: boolean
- reason: string explaining the decision
- addresses: array of individual addresses (empty if should_split is false)"""

            response = connect_wso2(
                access_token=access_token,
                user_content=prompt,
                system_prompt=system_prompt,
                prompt_type="address_splitting",
                max_tokens=1000
            )
            
            # Parse GPT response
            result = self._parse_gpt_response(response, address1, address2)
            result['method_used'] = 'gpt'
            
            return result
            
        except Exception as e:
            print(f"⚠️  GPT splitting failed: {str(e)}, falling back to rule-based")
            return self._rule_based_split(address1, address2)
    
    def _create_gpt_split_prompt(self, address1: str, address2: str = None) -> str:
        """
        Create the prompt for GPT address splitting
        """
        
        if address2 and address2.strip():
            prompt = f"""Analyze these address fields and determine if they contain multiple addresses that should be split:

Address Field 1: {address1}
Address Field 2: {address2}

Should these be split into multiple separate addresses? If yes, provide each individual address.

Return your response as a JSON object with this structure:
{{
    "should_split": true/false,
    "reason": "explanation of decision",
    "addresses": ["address1", "address2", ...]
}}"""
        else:
            prompt = f"""Analyze this address field and determine if it contains multiple addresses that should be split:

Address: {address1}

Should this be split into multiple separate addresses? If yes, provide each individual address.

Return your response as a JSON object with this structure:
{{
    "should_split": true/false,
    "reason": "explanation of decision",
    "addresses": ["address1", "address2", ...]
}}"""
        
        return prompt
    
    def _parse_gpt_response(self, response: str, address1: str, address2: str = None) -> Dict[str, Any]:
        """
        Parse the GPT response and extract split information
        """
        
        try:
            # Try to extract JSON from response
            # GPT might wrap it in markdown code blocks
            json_str = response
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
            
            result_data = json.loads(json_str)
            
            should_split = result_data.get('should_split', False)
            reason = result_data.get('reason', 'GPT analysis')
            addresses = result_data.get('addresses', [])
            
            # If should_split is True but no addresses provided, use original
            if should_split and not addresses:
                addresses = [address1]
                should_split = False
                reason = "GPT indicated split but provided no addresses"
            
            # If should_split is False, use original address
            if not should_split:
                addresses = [address1]
            
            return {
                'original_address1': address1,
                'original_address2': address2 if address2 else '',
                'should_split': should_split,
                'split_reason': reason,
                'addresses': addresses,
                'split_count': len(addresses)
            }
            
        except Exception as e:
            print(f"⚠️  Failed to parse GPT response: {str(e)}")
            print(f"   Raw response: {response[:200]}")
            
            # Fallback to rule-based
            return self._rule_based_split(address1, address2)


# Legacy method kept for backward compatibility
def analyze_and_split_legacy(address1: str, address2: str = None) -> Dict[str, Any]:
    """
    Legacy function that uses rule-based splitting only.
    Kept for backward compatibility.
    """
    splitter = AddressSplitter(use_gpt=False)
    return splitter.analyze_and_split(address1, address2)


def test_splitter(use_gpt: bool = False):
    """Test function to demonstrate the splitter functionality"""
    
    splitter = AddressSplitter(use_gpt=use_gpt)
    
    test_cases = [
        # No split cases
        ("211-245 Wheelhouse Lane", None, False),
        ("96-100 Pane Road", None, False),
        ("3800 West Ray Road Unit B3 (B15-B20)", None, False),
        ("6120 & 6132 Brookshire Blvd, Units M, N & F", None, False),
        ("140 Vann St NE, 1st Floor - 310/320", None, False),
        ("E of S Aspen Ave; S/S of E 91st S", None, False),
        ("NEQ OF THE SEQ OF SECTION 26, TOWNSHIP 15 SOUTH, RANGE 67 WEST OF THE 6TH P.M.", None, False),
        ("W/L of S. Rangerville Road, SW of S. Expressway 83", None, False),
        ("1/4 Mile South of 195th Ave SE on Kandi-Meeker Rd SE", None, False),
        ("Highway 40 and K", None, False),
        ("Main Street (Hwy 20)", None, False),
        
        # Potential split cases
        ("5250 NW 86th St, 8651, 8751, 8801 Northpark Dr", None, True),
        ("2905 S Regal St, 2908 E 29th Ave & 2917 S Regal St", None, True),
        ("8894 and 8896 Fort Smallwood Rd", None, True),
        ("34 Fairview St and 45 Oakwood Ave", None, True),
        ("10659 West Fairview Avenue & 1421 North Five Mile Road", None, True),
        ("2504 and 2506 Zeppelin Rd", "2510 and 2520 Aviation Way", True),
    ]
    
    print("=" * 80)
    mode = "GPT-Based" if use_gpt else "Rule-Based"
    print(f"Address Splitter Test Results ({mode})")
    print("=" * 80)
    
    pass_count = 0
    fail_count = 0
    
    for i, (addr1, addr2, expected_split) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Address1: {addr1}")
        if addr2:
            print(f"  Address2: {addr2}")
        
        result = splitter.analyze_and_split(addr1, addr2)
        
        print(f"  Should Split: {result['should_split']} (Expected: {expected_split})")
        print(f"  Reason: {result['split_reason']}")
        print(f"  Split Count: {result['split_count']}")
        print(f"  Method: {result['method_used']}")
        
        if result['should_split']:
            print(f"  Split Addresses:")
            for j, addr in enumerate(result['addresses'], 1):
                print(f"    {j}. {addr}")
        
        # Validation
        if result['should_split'] == expected_split:
            status = "✅ PASS"
            pass_count += 1
        else:
            status = "❌ FAIL"
            fail_count += 1
        print(f"  Status: {status}")
    
    print(f"\n{'='*80}")
    print(f"Test Summary: {pass_count} passed, {fail_count} failed out of {len(test_cases)} tests")
    print(f"{'='*80}")


if __name__ == "__main__":
    import sys
    
    # Check if --gpt flag is provided
    use_gpt = '--gpt' in sys.argv or '--use-gpt' in sys.argv
    
    if use_gpt:
        print("🤖 Running tests with GPT-based splitting\n")
    else:
        print("📋 Running tests with rule-based splitting (use --gpt flag for GPT mode)\n")
    
    test_splitter(use_gpt=use_gpt)
