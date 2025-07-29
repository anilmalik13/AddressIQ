#!/usr/bin/env python3
"""
Enhanced CSV Address Processor for AddressIQ
This script processes CSV files containing addresses and standardizes them using Azure OpenAI
"""

import pandas as pd
import json
import os
import sys
from typing import List, Dict, Any
import time
from datetime import datetime
import argparse
from pathlib import Path
import requests
from urllib.parse import quote

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.azure_openai import standardize_address, standardize_multiple_addresses

class CSVAddressProcessor:
    """
    A comprehensive CSV address processor that can:
    1. Read CSV files with address data
    2. Detect address columns automatically
    3. Standardize addresses using Azure OpenAI
    4. Add detailed standardization results
    5. Fill missing address components using free APIs
    6. Save enhanced CSV with original and standardized data
    """
    
    def __init__(self):
        self.supported_address_columns = [
            'address', 'full_address', 'street_address', 'mailing_address',
            'shipping_address', 'billing_address', 'location', 'addr',
            'property_address', 'site_address', 'address_line_1'
        ]
        
        # Define the specific column structure for your site data
        self.site_address_columns = {
            'site_name': 'SiteName',
            'address_1': 'Site_Address_1', 
            'address_2': 'Site_Address_2',
            'address_3': 'Site_Address_3',
            'city': 'City',
            'state': 'State', 
            'postcode': 'PostCode',
            'sno': 'S.NO'
        }
        
        # Free API configurations
        self.free_apis = {
            'nominatim': {
                'base_url': 'https://nominatim.openstreetmap.org/search',
                'rate_limit': 1.0,  # 1 second between requests
                'enabled': True
            },
            'geocodify': {
                'base_url': 'https://api.geocodify.com/v2/geocode',
                'rate_limit': 0.5,
                'enabled': True
            }
        }
        
    def detect_address_columns(self, df: pd.DataFrame) -> List[str]:
        """Automatically detect which columns contain addresses"""
        address_columns = []
        
        # Check for exact matches first
        for col in df.columns:
            if col.lower().strip() in self.supported_address_columns:
                address_columns.append(col)
        
        # Check for partial matches if no exact matches found
        if not address_columns:
            for col in df.columns:
                col_lower = col.lower().strip()
                if any(addr_keyword in col_lower for addr_keyword in ['address', 'addr', 'location']):
                    address_columns.append(col)
        
        return address_columns
    
    def detect_site_address_columns(self, df: pd.DataFrame) -> bool:
        """Check if the DataFrame has the specific site address column structure"""
        expected_columns = list(self.site_address_columns.values())
        available_columns = df.columns.tolist()
        
        # Check if all expected site address columns are present
        missing_columns = [col for col in expected_columns if col not in available_columns]
        
        if not missing_columns:
            print(f"✅ Detected site address column structure!")
            print(f"Found columns: {', '.join(expected_columns)}")
            return True
        else:
            print(f"❌ Missing site address columns: {', '.join(missing_columns)}")
            return False
    
    def combine_site_address_fields(self, row: pd.Series) -> str:
        """Combine separate site address fields into a single address string"""
        address_parts = []
        
        # Add address lines
        for addr_col in ['Site_Address_1', 'Site_Address_2', 'Site_Address_3']:
            if addr_col in row and pd.notna(row[addr_col]) and str(row[addr_col]).strip():
                address_parts.append(str(row[addr_col]).strip())
        
        # Add city
        if 'City' in row and pd.notna(row['City']) and str(row['City']).strip():
            address_parts.append(str(row['City']).strip())
            
        # Add state  
        if 'State' in row and pd.notna(row['State']) and str(row['State']).strip():
            address_parts.append(str(row['State']).strip())
            
        # Add postal code
        if 'PostCode' in row and pd.notna(row['PostCode']) and str(row['PostCode']).strip():
            address_parts.append(str(row['PostCode']).strip())
        
        # Join all parts with commas
        combined_address = ', '.join(address_parts)
        return combined_address if combined_address.strip() else ""
    
    def standardize_single_address(self, address: str, row_index: int, use_free_apis: bool = True) -> Dict[str, Any]:
        """Standardize a single address with error handling and optional free API enhancement"""
        try:
            if pd.isna(address) or not str(address).strip():
                return {
                    'status': 'skipped',
                    'reason': 'empty_address',
                    'formatted_address': '',
                    'confidence': 'n/a'
                }
            
            print(f"Processing row {row_index + 1}: {str(address)[:50]}...")
            
            # First, try Azure OpenAI standardization
            result = standardize_address(str(address).strip())
            
            if isinstance(result, dict) and 'formatted_address' in result:
                enhanced_result = {
                    'status': 'success',
                    'original_address': str(address),
                    'formatted_address': result.get('formatted_address', ''),
                    'street_number': result.get('street_number', ''),
                    'street_name': result.get('street_name', ''),
                    'street_type': result.get('street_type', ''),
                    'unit_type': result.get('unit_type', ''),
                    'unit_number': result.get('unit_number', ''),
                    'city': result.get('city', ''),
                    'state': result.get('state', ''),
                    'postal_code': result.get('postal_code', ''),
                    'country': result.get('country', ''),
                    'confidence': result.get('confidence', 'unknown'),
                    'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                    'api_source': 'azure_openai',
                    'latitude': '',
                    'longitude': ''
                }
                
                # Try to enhance with free APIs if enabled
                if use_free_apis:
                    enhanced_result = self.fill_missing_components_with_free_apis(str(address), enhanced_result)
                
                return enhanced_result
            else:
                # If Azure OpenAI fails, try free APIs as primary source
                if use_free_apis:
                    print(f"   ⚠️  Azure OpenAI failed, trying free APIs...")
                    fallback_result = {
                        'status': 'partial',
                        'original_address': str(address),
                        'formatted_address': str(address),
                        'street_number': '',
                        'street_name': '',
                        'street_type': '',
                        'unit_type': '',
                        'unit_number': '',
                        'city': '',
                        'state': '',
                        'postal_code': '',
                        'country': '',
                        'confidence': 'low',
                        'issues': 'azure_openai_failed',
                        'api_source': 'fallback',
                        'latitude': '',
                        'longitude': ''
                    }
                    
                    return self.fill_missing_components_with_free_apis(str(address), fallback_result)
                
                return {
                    'status': 'error',
                    'reason': 'invalid_response',
                    'original_address': str(address),
                    'formatted_address': str(address),
                    'confidence': 'low'
                }
                
        except Exception as e:
            print(f"Error processing address '{address}': {str(e)}")
            return {
                'status': 'error',
                'reason': f'processing_error: {str(e)}',
                'original_address': str(address),
                'formatted_address': str(address),
                'confidence': 'low'
            }
    
    def process_csv_file(self, input_file: str, output_file: str = None, 
                        address_column: str = None, batch_size: int = 5, 
                        use_free_apis: bool = True) -> str:
        """
        Process a CSV file and standardize addresses
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            address_column: Specific column name containing addresses (optional)
            batch_size: Number of addresses to process in each batch
            use_free_apis: Whether to use free APIs to fill missing components
        
        Returns:
            Path to the output file
        """
        
        # Validate input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load CSV
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding='latin-1')
            except Exception as e:
                raise Exception(f"Could not read CSV file: {str(e)}")
        
        print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        
        if use_free_apis:
            print(f"🌐 Free API enhancement: ENABLED")
            print(f"   Available APIs: {', '.join([k for k, v in self.free_apis.items() if v['enabled']])}")
        else:
            print(f"🌐 Free API enhancement: DISABLED")
        
        # Check if this is a site address structure
        is_site_format = self.detect_site_address_columns(df)
        
        if is_site_format:
            # Process site address format
            return self.process_site_address_format(df, output_file, use_free_apis)
        else:
            # Process regular address format
            return self.process_regular_address_format(df, address_column, output_file, use_free_apis)
    
    def process_site_address_format(self, df: pd.DataFrame, output_file: str = None, use_free_apis: bool = True) -> str:
        """Process CSV with site address column structure"""
        
        print(f"\n🏢 Processing Site Address Format")
        print("=" * 50)
        print("📋 Processing mode: ADD STANDARDIZED COLUMNS")
        print("   Original columns preserved + new standardized columns added")
        
        # Add combined address column
        df['Combined_Address'] = df.apply(self.combine_site_address_fields, axis=1)
        
        # Add standardization result columns (including new API-related columns)
        base_col_name = "Standardized_Address"
        df[f"{base_col_name}_formatted"] = ""
        df[f"{base_col_name}_street_number"] = ""
        df[f"{base_col_name}_street_name"] = ""
        df[f"{base_col_name}_street_type"] = ""
        df[f"{base_col_name}_unit_type"] = ""
        df[f"{base_col_name}_unit_number"] = ""
        df[f"{base_col_name}_city"] = ""
        df[f"{base_col_name}_state"] = ""
        df[f"{base_col_name}_postal_code"] = ""
        df[f"{base_col_name}_country"] = ""
        df[f"{base_col_name}_confidence"] = ""
        df[f"{base_col_name}_issues"] = ""
        df[f"{base_col_name}_status"] = ""
        df[f"{base_col_name}_api_source"] = ""
        df[f"{base_col_name}_latitude"] = ""
        df[f"{base_col_name}_longitude"] = ""
        
        # Process each row
        total_rows = len(df)
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            combined_address = row['Combined_Address']
            
            if not combined_address.strip():
                print(f"Row {index + 1}: Skipping empty address")
                processed_count += 1
                continue
                
            result = self.standardize_single_address(combined_address, index, use_free_apis)
            
            # Update DataFrame with results
            df.at[index, f"{base_col_name}_formatted"] = result.get('formatted_address', '')
            df.at[index, f"{base_col_name}_street_number"] = result.get('street_number', '')
            df.at[index, f"{base_col_name}_street_name"] = result.get('street_name', '')
            df.at[index, f"{base_col_name}_street_type"] = result.get('street_type', '')
            df.at[index, f"{base_col_name}_unit_type"] = result.get('unit_type', '')
            df.at[index, f"{base_col_name}_unit_number"] = result.get('unit_number', '')
            df.at[index, f"{base_col_name}_city"] = result.get('city', '')
            df.at[index, f"{base_col_name}_state"] = result.get('state', '')
            df.at[index, f"{base_col_name}_postal_code"] = result.get('postal_code', '')
            df.at[index, f"{base_col_name}_country"] = result.get('country', '')
            df.at[index, f"{base_col_name}_confidence"] = result.get('confidence', '')
            df.at[index, f"{base_col_name}_issues"] = result.get('issues', '')
            df.at[index, f"{base_col_name}_status"] = result.get('status', '')
            df.at[index, f"{base_col_name}_api_source"] = result.get('api_source', '')
            df.at[index, f"{base_col_name}_latitude"] = result.get('latitude', '')
            df.at[index, f"{base_col_name}_longitude"] = result.get('longitude', '')
            
            processed_count += 1
            if result.get('status') == 'success':
                success_count += 1
            else:
                error_count += 1
            
            # Progress indicator
            if processed_count % 5 == 0:
                print(f"Progress: {processed_count}/{total_rows} ({processed_count/total_rows*100:.1f}%)")
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        return self.save_and_summarize_results(df, output_file, processed_count, success_count, error_count, ["Combined_Address"])
    
    def process_regular_address_format(self, df: pd.DataFrame, address_column: str = None, output_file: str = None, use_free_apis: bool = True) -> str:
        """Process CSV with regular address format"""
        
        # Detect address columns
        if address_column:
            if address_column not in df.columns:
                raise ValueError(f"Specified address column '{address_column}' not found in CSV")
            address_columns = [address_column]
        else:
            address_columns = self.detect_address_columns(df)
            
        if not address_columns:
            print("Available columns:", df.columns.tolist())
            raise ValueError("No address columns detected. Please specify the address column manually.")
        
        print(f"Detected address columns: {', '.join(address_columns)}")
        
        # Process each address column
        total_processed = 0
        total_success = 0
        total_errors = 0
        
        for addr_col in address_columns:
            print(f"\nProcessing column: {addr_col}")
            print("=" * 50)
            
            # Add new columns for standardized data
            base_col_name = f"{addr_col}_standardized"
            df[f"{base_col_name}_formatted"] = ""
            df[f"{base_col_name}_street_number"] = ""
            df[f"{base_col_name}_street_name"] = ""
            df[f"{base_col_name}_street_type"] = ""
            df[f"{base_col_name}_unit_type"] = ""
            df[f"{base_col_name}_unit_number"] = ""
            df[f"{base_col_name}_city"] = ""
            df[f"{base_col_name}_state"] = ""
            df[f"{base_col_name}_postal_code"] = ""
            df[f"{base_col_name}_country"] = ""
            df[f"{base_col_name}_confidence"] = ""
            df[f"{base_col_name}_issues"] = ""
            df[f"{base_col_name}_status"] = ""
            df[f"{base_col_name}_api_source"] = ""
            df[f"{base_col_name}_latitude"] = ""
            df[f"{base_col_name}_longitude"] = ""
            
            # Process addresses in batches
            total_rows = len(df)
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                address = row[addr_col]
                result = self.standardize_single_address(address, index, use_free_apis)
                
                # Update DataFrame with results
                df.at[index, f"{base_col_name}_formatted"] = result.get('formatted_address', '')
                df.at[index, f"{base_col_name}_street_number"] = result.get('street_number', '')
                df.at[index, f"{base_col_name}_street_name"] = result.get('street_name', '')
                df.at[index, f"{base_col_name}_street_type"] = result.get('street_type', '')
                df.at[index, f"{base_col_name}_unit_type"] = result.get('unit_type', '')
                df.at[index, f"{base_col_name}_unit_number"] = result.get('unit_number', '')
                df.at[index, f"{base_col_name}_city"] = result.get('city', '')
                df.at[index, f"{base_col_name}_state"] = result.get('state', '')
                df.at[index, f"{base_col_name}_postal_code"] = result.get('postal_code', '')
                df.at[index, f"{base_col_name}_country"] = result.get('country', '')
                df.at[index, f"{base_col_name}_confidence"] = result.get('confidence', '')
                df.at[index, f"{base_col_name}_issues"] = result.get('issues', '')
                df.at[index, f"{base_col_name}_status"] = result.get('status', '')
                df.at[index, f"{base_col_name}_api_source"] = result.get('api_source', '')
                df.at[index, f"{base_col_name}_latitude"] = result.get('latitude', '')
                df.at[index, f"{base_col_name}_longitude"] = result.get('longitude', '')
                
                processed_count += 1
                if result.get('status') == 'success':
                    success_count += 1
                else:
                    error_count += 1
                
                # Progress indicator
                if processed_count % 10 == 0:
                    print(f"Progress: {processed_count}/{total_rows} ({processed_count/total_rows*100:.1f}%)")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            total_processed += processed_count
            total_success += success_count
            total_errors += error_count
        
        return self.save_and_summarize_results(df, output_file, total_processed, total_success, total_errors, address_columns)
    
    def save_and_summarize_results(self, df: pd.DataFrame, output_file: str, processed_count: int, success_count: int, error_count: int, address_columns: List[str]) -> str:
        """Save results and display summary"""
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"addresses_standardized_{timestamp}.csv"
        
        # Save results
        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
        except Exception as e:
            # Fallback to latin-1 encoding if utf-8 fails
            df.to_csv(output_file, index=False, encoding='latin-1')
        
        # Print summary
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Output file: {output_file}")
        print(f"Total rows processed: {processed_count}")
        print(f"Successful standardizations: {success_count}")
        print(f"Errors/Skipped: {error_count}")
        print(f"Success rate: {success_count/processed_count*100:.1f}%" if processed_count > 0 else "N/A")
        print(f"Address columns processed: {', '.join(address_columns)}")
        
        return output_file

    def geocode_with_nominatim(self, address: str) -> Dict[str, Any]:
        """Geocode using OpenStreetMap Nominatim (free, no API key required)"""
        try:
            params = {
                'q': address,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1
            }
            
            headers = {
                'User-Agent': 'AddressIQ-Processor/1.0 (contact@addressiq.com)'
            }
            
            response = requests.get(
                self.free_apis['nominatim']['base_url'],
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    result = data[0]
                    address_parts = result.get('address', {})
                    
                    lat = result.get('lat', '')
                    lon = result.get('lon', '')
                    
                    return {
                        'success': True,
                        'source': 'nominatim',
                        'formatted_address': result.get('display_name', ''),
                        'street_number': address_parts.get('house_number', ''),
                        'street_name': address_parts.get('road', ''),
                        'city': address_parts.get('city') or address_parts.get('town') or address_parts.get('village', ''),
                        'state': address_parts.get('state', ''),
                        'postal_code': address_parts.get('postcode', ''),
                        'country': address_parts.get('country', ''),
                        'latitude': lat,
                        'longitude': lon,
                        'confidence': 'medium'
                    }
            
            return {'success': False, 'error': f'No results found for: {address}'}
            
        except Exception as e:
            return {'success': False, 'error': f'Nominatim API error: {str(e)}'}
    
    def geocode_with_geocodify(self, address: str) -> Dict[str, Any]:
        """Geocode using Geocodify API (free tier available)"""
        try:
            params = {
                'api_key': 'demo',  # Free demo key with limitations
                'q': address
            }
            
            response = requests.get(
                self.free_apis['geocodify']['base_url'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response', {}).get('features'):
                    result = data['response']['features'][0]
                    properties = result.get('properties', {})
                    geometry = result.get('geometry', {})
                    coordinates = geometry.get('coordinates', [])
                    
                    # Geocodify returns coordinates as [longitude, latitude]
                    latitude = coordinates[1] if len(coordinates) > 1 else ''
                    longitude = coordinates[0] if len(coordinates) > 0 else ''
                    
                    return {
                        'success': True,
                        'source': 'geocodify',
                        'formatted_address': properties.get('label', ''),
                        'street_number': properties.get('housenumber', ''),
                        'street_name': properties.get('street', ''),
                        'city': properties.get('city', ''),
                        'state': properties.get('state', ''),
                        'postal_code': properties.get('postalcode', ''),
                        'country': properties.get('country', ''),
                        'latitude': str(latitude) if latitude else '',
                        'longitude': str(longitude) if longitude else '',
                        'confidence': 'medium'
                    }
            
            return {'success': False, 'error': f'No results found for: {address}'}
            
        except Exception as e:
            return {'success': False, 'error': f'Geocodify API error: {str(e)}'}
    
    def create_simplified_address_for_geocoding(self, current_result: Dict[str, Any]) -> List[str]:
        """Create simplified address variants for better geocoding success"""
        simplified_addresses = []
        
        # Extract basic components
        street_number = current_result.get('street_number', '').strip()
        street_name = current_result.get('street_name', '').strip()
        street_type = current_result.get('street_type', '').strip()
        city = current_result.get('city', '').strip()
        state = current_result.get('state', '').strip()
        postal_code = current_result.get('postal_code', '').strip()
        country = current_result.get('country', '').strip()
        
        # Strategy 1: Basic street address + city + postal code (most likely to work)
        if street_name and city and postal_code:
            basic_parts = []
            if street_number:
                basic_parts.append(street_number)
            basic_parts.append(street_name)
            if street_type:
                basic_parts.append(street_type)
            basic_parts.extend([city, postal_code])
            simplified_addresses.append(' '.join(basic_parts))
        
        # Strategy 2: Just city + postal code (fallback for area coordinates)
        if city and postal_code:
            simplified_addresses.append(f"{city} {postal_code}")
        
        # Strategy 3: Just postal code (minimal fallback)
        if postal_code:
            simplified_addresses.append(postal_code)
        
        return simplified_addresses

    def fill_missing_components_with_free_apis(self, address: str, current_result: Dict[str, Any]) -> Dict[str, Any]:
        """Try to fill missing address components using free APIs with simplified address strategy"""
        
        # Check if we need to fill missing components
        missing_components = []
        key_components = ['street_number', 'street_name', 'city', 'state', 'postal_code']
        
        for component in key_components:
            if not current_result.get(component, '').strip():
                missing_components.append(component)
        
        # Always try to get coordinates if they're not present
        need_coordinates = not current_result.get('latitude', '').strip()
        
        if not missing_components and not need_coordinates:
            return current_result  # Nothing to fill
        
        # Create simplified addresses for geocoding
        simplified_addresses = self.create_simplified_address_for_geocoding(current_result)
        
        # If we have parsed components, try simplified addresses first
        if simplified_addresses:
            for i, simplified_addr in enumerate(simplified_addresses):
                if self.free_apis['nominatim']['enabled']:
                    time.sleep(self.free_apis['nominatim']['rate_limit'])
                    
                    nominatim_result = self.geocode_with_nominatim(simplified_addr)
                    if nominatim_result.get('success'):
                        # Fill missing components (but keep existing ones)
                        for component in missing_components:
                            if nominatim_result.get(component, '').strip():
                                current_result[component] = nominatim_result[component]
                        
                        # Always update coordinates if available
                        if nominatim_result.get('latitude', '').strip():
                            current_result['latitude'] = nominatim_result['latitude']
                            current_result['longitude'] = nominatim_result['longitude']
                        
                        # Update metadata
                        current_result['api_source'] = f"{current_result.get('api_source', '')}_enhanced_by_nominatim_simplified".strip('_')
                        return current_result
        
        # Fallback: Try original full address
        
        if self.free_apis['nominatim']['enabled']:
            time.sleep(self.free_apis['nominatim']['rate_limit'])
            
            nominatim_result = self.geocode_with_nominatim(address)
            if nominatim_result.get('success'):
                # Fill missing components
                for component in missing_components:
                    if nominatim_result.get(component, '').strip():
                        current_result[component] = nominatim_result[component]
                
                # Always update coordinates if available
                if nominatim_result.get('latitude', '').strip():
                    current_result['latitude'] = nominatim_result['latitude']
                    current_result['longitude'] = nominatim_result['longitude']
                
                # Update metadata
                current_result['api_source'] = f"{current_result.get('api_source', '')}_enhanced_by_nominatim".strip('_')
                return current_result
        
        # Try Geocodify as final fallback
        if self.free_apis['geocodify']['enabled']:
            time.sleep(self.free_apis['geocodify']['rate_limit'])
            
            geocodify_result = self.geocode_with_geocodify(address)
            if geocodify_result.get('success'):
                # Fill remaining missing components
                for component in missing_components:
                    if not current_result.get(component, '').strip() and geocodify_result.get(component, '').strip():
                        current_result[component] = geocodify_result[component]
                
                # Add coordinates if not already present
                if need_coordinates and geocodify_result.get('latitude', '').strip():
                    current_result['latitude'] = geocodify_result['latitude']
                    current_result['longitude'] = geocodify_result['longitude']
                
                # Update metadata
                current_result['api_source'] = f"{current_result.get('api_source', '')}_enhanced_by_geocodify".strip('_')
        
        return current_result
    
    def configure_free_apis(self, nominatim: bool = True, geocodify: bool = True):
        """Configure which free APIs to use"""
        self.free_apis['nominatim']['enabled'] = nominatim
        self.free_apis['geocodify']['enabled'] = geocodify
        
        enabled_apis = [name for name, config in self.free_apis.items() if config['enabled']]
        print(f"📡 Configured free APIs: {', '.join(enabled_apis) if enabled_apis else 'None'}")
    
    def test_free_apis(self):
        """Test the free APIs with a sample address"""
        test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
        print(f"🧪 Testing free APIs with: {test_address}")
        print("=" * 50)
        
        if self.free_apis['nominatim']['enabled']:
            print("Testing Nominatim...")
            result = self.geocode_with_nominatim(test_address)
            if result.get('success'):
                print(f"✅ Nominatim: {result.get('formatted_address', 'N/A')}")
                print(f"   Coordinates: {result.get('latitude', 'N/A')}, {result.get('longitude', 'N/A')}")
                print(f"   Components: {result.get('street_number', '')}, {result.get('street_name', '')}, {result.get('city', '')}")
            else:
                print(f"❌ Nominatim: {result.get('error', 'Unknown error')}")
        
        if self.free_apis['geocodify']['enabled']:
            print("Testing Geocodify...")
            time.sleep(1)  # Rate limiting
            result = self.geocode_with_geocodify(test_address)
            if result.get('success'):
                print(f"✅ Geocodify: {result.get('formatted_address', 'N/A')}")
                print(f"   Coordinates: {result.get('latitude', 'N/A')}, {result.get('longitude', 'N/A')}")
            else:
                print(f"❌ Geocodify: {result.get('error', 'Unknown error')}")
    
    def parse_standardized_address_to_columns(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Parse standardized address result back to column structure"""
        components = {}
        
        # Build street address from components
        street_parts = []
        if result.get('street_number') and result.get('street_number') != 'null':
            street_parts.append(str(result['street_number']))
        if result.get('street_name') and result.get('street_name') != 'null':
            street_parts.append(str(result['street_name']))
        if result.get('street_type') and result.get('street_type') != 'null':
            street_parts.append(str(result['street_type']))
        
        components['street_address'] = ' '.join(street_parts) if street_parts else ''
        
        # Build unit information
        unit_parts = []
        if result.get('unit_type') and result.get('unit_type') != 'null':
            unit_parts.append(str(result['unit_type']))
        if result.get('unit_number') and result.get('unit_number') != 'null':
            unit_parts.append(str(result['unit_number']))
        
        components['unit_info'] = ' '.join(unit_parts) if unit_parts else ''
        
        # Direct mappings with null checking
        components['city'] = str(result.get('city', '')) if result.get('city') and result.get('city') != 'null' else ''
        components['state'] = str(result.get('state', '')) if result.get('state') and result.get('state') != 'null' else ''
        components['postal_code'] = str(result.get('postal_code', '')) if result.get('postal_code') and result.get('postal_code') != 'null' else ''
        
        return components
    
def main():
    """Command line interface for the CSV Address Processor"""
    parser = argparse.ArgumentParser(description='Process CSV files to standardize addresses')
    parser.add_argument('input_file', nargs='?', help='Path to input CSV file')
    parser.add_argument('-o', '--output', help='Path to output CSV file (optional)')
    parser.add_argument('-c', '--column', help='Specific address column name (optional)')
    parser.add_argument('-b', '--batch-size', type=int, default=5, help='Batch size for processing (default: 5)')
    parser.add_argument('--no-free-apis', action='store_true', help='Disable free API enhancement')
    parser.add_argument('--test-apis', action='store_true', help='Test free APIs and exit')
    
    args = parser.parse_args()
    
    # Create processor instance
    processor = CSVAddressProcessor()
    
    # Test APIs if requested
    if args.test_apis:
        processor.test_free_apis()
        return
    
    # Validate input file is provided for processing
    if not args.input_file:
        print("❌ Error: input_file is required for processing")
        parser.print_help()
        sys.exit(1)
    
    try:
        print("🏠 AddressIQ CSV Processor")
        print("=" * 40)
        print(f"Input file: {args.input_file}")
        
        # Process the CSV file
        output_file = processor.process_csv_file(
            input_file=args.input_file,
            output_file=args.output,
            address_column=args.column,
            batch_size=args.batch_size,
            use_free_apis=not args.no_free_apis
        )
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📁 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
