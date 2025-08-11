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

# Import Azure SQL Database service
try:
    from app.services.azure_sql_database import AzureSQLDatabaseService
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Azure SQL Database service not available: {str(e)}")
    DATABASE_AVAILABLE = False

class CSVAddressProcessor:
    """
    A comprehensive address processor that can:
    1. Read CSV files with address data
    2. Process single addresses directly
    3. Process multiple addresses from input
    4. Detect address columns automatically
    5. Standardize addresses using Azure OpenAI
    6. Add detailed standardization results
    7. Fill missing address components using free APIs
    8. Save enhanced CSV with original and standardized data
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
        
        # Initialize database service
        if DATABASE_AVAILABLE:
            try:
                self.db_service = AzureSQLDatabaseService()
                
                # Print database stats on initialization
                stats = self.db_service.get_database_stats()
                print(f"💾 Azure SQL Database Stats: {stats['total_unique_addresses']} unique addresses, "
                      f"{stats['total_address_lookups']} total lookups, "
                      f"{stats['cache_hit_rate']:.1f}% cache hit rate")
            except Exception as e:
                print(f"❌ Failed to initialize Azure SQL Database: {str(e)}")
                self.db_service = None
        else:
            self.db_service = None
            print("⚠️  Running without database caching")
    
    def process_single_address_input(self, address: str, country: str = None, output_format: str = 'json') -> Dict[str, Any]:
        """
        Process a single address input
        
        Args:
            address: The address string to process
            country: Optional country for country-specific formatting
            output_format: 'json', 'formatted', or 'detailed'
        
        Returns:
            Dictionary containing the standardized address data
        """
        print(f"\n🏠 Processing address: {address}")
        if country:
            print(f"🌍 Target country: {country}")
        print("=" * 50)
        
        # Check database cache first
        if self.db_service:
            existing_address = self.db_service.find_existing_address(address)
            if existing_address:
                print("💾 Found in database cache!")
                # Ensure cached result has proper status and required fields
                cached_result = {
                    'status': 'success',
                    'original_address': address,
                    'formatted_address': existing_address.get('formatted_address', ''),
                    'street_number': existing_address.get('street_number', '') or '',
                    'street_name': existing_address.get('street_name', '') or '',
                    'street_type': existing_address.get('street_type', '') or '',
                    'unit_type': existing_address.get('unit_type', '') or '',
                    'unit_number': existing_address.get('unit_number', '') or '',
                    'city': existing_address.get('city', '') or '',
                    'state': existing_address.get('state', '') or '',
                    'postal_code': existing_address.get('postal_code', '') or '',
                    'country': existing_address.get('country', '') or '',
                    'confidence': existing_address.get('confidence', 'medium') or 'medium',
                    'issues': existing_address.get('issues', '') or '',
                    'api_source': f"{existing_address.get('api_source', 'cached')}_cached",
                    'latitude': str(existing_address.get('latitude', '')) if existing_address.get('latitude') else '',
                    'longitude': str(existing_address.get('longitude', '')) if existing_address.get('longitude') else '',
                    'address_id': existing_address.get('id'),
                    'from_cache': True
                }
                return self._format_output(cached_result, output_format)
        
        # Process with AI
        try:
            print("🤖 Processing with AI...")
            result = standardize_address(address)
            
            # Check if we got a valid result (not an error)
            if result and not result.get('error') and result.get('formatted_address'):
                print("✅ AI processing successful")
                
                # Add required fields for our system
                enhanced_result = {
                    'status': 'success',
                    'original_address': address,
                    'formatted_address': result.get('formatted_address', ''),
                    'street_number': result.get('street_number', '') or '',
                    'street_name': result.get('street_name', '') or '',
                    'street_type': result.get('street_type', '') or '',
                    'unit_type': result.get('unit_type', '') or '',
                    'unit_number': result.get('unit_number', '') or '',
                    'city': result.get('city', '') or '',
                    'state': result.get('state', '') or '',
                    'postal_code': result.get('postal_code', '') or '',
                    'country': result.get('country', '') or '',
                    'confidence': result.get('confidence', 'medium') or 'medium',
                    'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                    'api_source': 'azure_openai',
                    'latitude': '',
                    'longitude': '',
                    'from_cache': False
                }
                
                # Save to database
                if self.db_service:
                    try:
                        address_id = self.db_service.save_address(address, enhanced_result)
                        enhanced_result['address_id'] = address_id
                        print(f"💾 Saved to database with ID: {address_id}")
                    except Exception as e:
                        print(f"⚠️ Could not save to database: {e}")
                        enhanced_result['address_id'] = None
                
                return self._format_output(enhanced_result, output_format)
            else:
                print("❌ AI processing failed")
                error_msg = result.get('error', 'AI processing failed') if result else 'No response received'
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'original_address': address,
                    'from_cache': False
                }
                
        except Exception as e:
            print(f"❌ Error processing address: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'original_address': address,
                'from_cache': False
            }

    def process_multiple_addresses_input(self, addresses: List[str], country: str = None, output_format: str = 'json') -> List[Dict[str, Any]]:
        """
        Process multiple addresses from direct input
        
        Args:
            addresses: List of address strings
            country: Optional country for country-specific formatting
            output_format: 'json', 'formatted', or 'detailed'
        
        Returns:
            List of dictionaries containing standardized address data
        """
        print(f"\n🏠 Processing {len(addresses)} addresses")
        if country:
            print(f"🌍 Target country: {country}")
        print("=" * 50)
        
        results = []
        
        # Check which addresses are already in cache
        cached_addresses = []
        new_addresses = []
        
        for i, address in enumerate(addresses):
            if self.db_service:
                existing = self.db_service.find_existing_address(address)
                if existing:
                    # Ensure cached result has proper status and required fields
                    cached_result = {
                        'status': 'success',
                        'original_address': address,
                        'formatted_address': existing.get('formatted_address', ''),
                        'street_number': existing.get('street_number', '') or '',
                        'street_name': existing.get('street_name', '') or '',
                        'street_type': existing.get('street_type', '') or '',
                        'unit_type': existing.get('unit_type', '') or '',
                        'unit_number': existing.get('unit_number', '') or '',
                        'city': existing.get('city', '') or '',
                        'state': existing.get('state', '') or '',
                        'postal_code': existing.get('postal_code', '') or '',
                        'country': existing.get('country', '') or '',
                        'confidence': existing.get('confidence', 'medium') or 'medium',
                        'issues': existing.get('issues', '') or '',
                        'api_source': f"{existing.get('api_source', 'cached')}_cached",
                        'latitude': str(existing.get('latitude', '')) if existing.get('latitude') else '',
                        'longitude': str(existing.get('longitude', '')) if existing.get('longitude') else '',
                        'address_id': existing.get('id'),
                        'from_cache': True
                    }
                    cached_addresses.append((i, cached_result))
                else:
                    new_addresses.append((i, address))
            else:
                new_addresses.append((i, address))
        
        print(f"💾 Found {len(cached_addresses)} addresses in cache")
        print(f"🤖 Processing {len(new_addresses)} new addresses")
        
        # Initialize results array
        results = [None] * len(addresses)
        
        # Add cached results
        for original_index, cached_result in cached_addresses:
            results[original_index] = self._format_output(cached_result, output_format)
        
        # Process new addresses in batches
        if new_addresses:
            new_address_strings = [addr for _, addr in new_addresses]
            
            try:
                ai_results = standardize_multiple_addresses(new_address_strings, use_batch=True)
                
                for i, (original_index, address) in enumerate(new_addresses):
                    if i < len(ai_results):
                        ai_result = ai_results[i]
                        
                        # Convert AI result to our expected format
                        if ai_result and not ai_result.get('error') and ai_result.get('formatted_address'):
                            result = {
                                'status': 'success',
                                'original_address': address,
                                'formatted_address': ai_result.get('formatted_address', ''),
                                'street_number': ai_result.get('street_number', '') or '',
                                'street_name': ai_result.get('street_name', '') or '',
                                'street_type': ai_result.get('street_type', '') or '',
                                'unit_type': ai_result.get('unit_type', '') or '',
                                'unit_number': ai_result.get('unit_number', '') or '',
                                'city': ai_result.get('city', '') or '',
                                'state': ai_result.get('state', '') or '',
                                'postal_code': ai_result.get('postal_code', '') or '',
                                'country': ai_result.get('country', '') or '',
                                'confidence': ai_result.get('confidence', 'medium') or 'medium',
                                'issues': ', '.join(ai_result.get('issues', [])) if ai_result.get('issues') else '',
                                'api_source': 'azure_openai_batch',
                                'latitude': '',
                                'longitude': '',
                                'from_cache': False
                            }
                        else:
                            # Failed processing
                            error_msg = ai_result.get('error', 'AI processing failed') if ai_result else 'No response received'
                            result = {
                                'status': 'failed',
                                'error': error_msg,
                                'original_address': address,
                                'from_cache': False
                            }
                        
                        # Save successful results to database
                        if result.get('status') == 'success' and self.db_service:
                            try:
                                address_id = self.db_service.save_address(address, result)
                                result['address_id'] = address_id
                                print(f"💾 Saved address {i+1} to database with ID: {address_id}")
                            except Exception as e:
                                print(f"⚠️ Could not save address {i+1}: {e}")
                                result['address_id'] = None
                        
                        results[original_index] = self._format_output(result, output_format)
                    else:
                        # Fallback for missing results
                        results[original_index] = self._format_output({
                            'status': 'failed',
                            'error': 'No result from AI',
                            'original_address': address,
                            'from_cache': False
                        }, output_format)
                        
            except Exception as e:
                print(f"❌ Error in batch processing: {e}")
                # Fallback to individual processing
                for original_index, address in new_addresses:
                    results[original_index] = self.process_single_address_input(address, country, output_format)
        
        return results

    def _format_output(self, result: Dict[str, Any], output_format: str) -> Dict[str, Any]:
        """Format the output based on the requested format"""
        if output_format == 'formatted':
            return {
                'original_address': result.get('original_address', ''),
                'formatted_address': result.get('formatted_address', ''),
                'confidence': result.get('confidence', ''),
                'from_cache': result.get('from_cache', False),
                'status': result.get('status', 'unknown')
            }
        elif output_format == 'detailed':
            return result  # Return full result
        else:  # json format (default)
            return result
        
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
    
    def detect_country_column(self, df: pd.DataFrame) -> str:
        """Detect if CSV has a country column"""
        country_columns = [
            'country', 'Country', 'COUNTRY', 'nation', 'Nation', 'NATION',
            'country_code', 'Country_Code', 'COUNTRY_CODE', 'country_name',
            'Country_Name', 'COUNTRY_NAME', 'iso_country', 'ISO_Country'
        ]
        
        for col in country_columns:
            if col in df.columns:
                print(f"✅ Detected country column: '{col}'")
                return col
        
        print("ℹ️  No country column detected - will use address-based detection")
        return None
    
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
    
    def standardize_single_address(self, address: str, row_index: int, target_country: str = None, use_free_apis: bool = True) -> Dict[str, Any]:
        """Standardize a single address with database caching and error handling"""
        try:
            if pd.isna(address) or not str(address).strip():
                return {
                    'status': 'skipped',
                    'reason': 'empty_address',
                    'formatted_address': '',
                    'confidence': 'n/a',
                    'address_id': None,
                    'from_cache': False
                }
            
            address_str = str(address).strip()
            print(f"Processing row {row_index + 1}: {address_str[:50]}...")
            
            # Check if address exists in database first (only use successfully processed addresses)
            if self.db_service:
                existing_address = self.db_service.find_existing_address(address_str)
                
                if existing_address:
                    # Only use cached result if it was successfully processed (not fallback data)
                    if (existing_address.get('api_source') != 'fallback' and 
                        existing_address.get('issues') != 'azure_openai_failed' and
                        existing_address.get('confidence') != 'low'):
                        
                        print(f"   ✅ Found cached address (ID: {existing_address['id']}, used {existing_address['usage_count']} times)")
                        result = {
                            'status': 'success',
                            'original_address': address_str,
                            'formatted_address': existing_address['formatted_address'],
                            'street_number': existing_address['street_number'] or '',
                            'street_name': existing_address['street_name'] or '',
                            'street_type': existing_address['street_type'] or '',
                            'unit_type': existing_address['unit_type'] or '',
                            'unit_number': existing_address['unit_number'] or '',
                            'city': existing_address['city'] or '',
                            'state': existing_address['state'] or '',
                            'postal_code': existing_address['postal_code'] or '',
                            'country': existing_address['country'] or '',
                            'confidence': existing_address['confidence'] or '',
                            'issues': existing_address['issues'] or '',
                            'api_source': f"{existing_address['api_source']}_cached" if existing_address['api_source'] else 'cached',
                            'latitude': str(existing_address['latitude']) if existing_address['latitude'] else '',
                            'longitude': str(existing_address['longitude']) if existing_address['longitude'] else '',
                            'address_id': existing_address['id'],
                            'from_cache': True
                        }
                        return result
                    else:
                        print(f"   ⚠️  Found cached address but it's fallback data (ID: {existing_address['id']}) - processing with AI...")
            
            # If not in database, process with AI model
            print(f"   🤖 Processing with AI model...")
            if target_country:
                print(f"   🌍 Using country-specific formatting for: {target_country}")
            result = standardize_address(address_str, target_country)
            
            if isinstance(result, dict) and 'formatted_address' in result:
                enhanced_result = {
                    'status': 'success',
                    'original_address': address_str,
                    'formatted_address': str(result.get('formatted_address', '')),
                    'street_number': str(result.get('street_number', '') or ''),
                    'street_name': str(result.get('street_name', '') or ''),
                    'street_type': str(result.get('street_type', '') or ''),
                    'unit_type': str(result.get('unit_type', '') or ''),
                    'unit_number': str(result.get('unit_number', '') or ''),
                    'city': str(result.get('city', '') or ''),
                    'state': str(result.get('state', '') or ''),
                    'postal_code': str(result.get('postal_code', '') or ''),
                    'country': str(result.get('country', '') or ''),
                    'confidence': result.get('confidence', 'unknown'),
                    'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                    'api_source': 'azure_openai',
                    'latitude': '',
                    'longitude': '',
                    'from_cache': False
                }
                
                # Try to enhance with free APIs if enabled
                if use_free_apis:
                    enhanced_result = self.fill_missing_components_with_free_apis(address_str, enhanced_result)
                
                # Save to database only if successfully processed by OpenAI
                if self.db_service:
                    address_id = self.db_service.save_address(address_str, enhanced_result)
                    enhanced_result['address_id'] = address_id
                    print(f"   💾 Saved to Azure SQL Database (ID: {address_id})")
                else:
                    enhanced_result['address_id'] = None
                    print(f"   ⚠️  Database not available - result not cached")
                
                return enhanced_result
            else:
                # If Azure OpenAI fails, try free APIs as primary source
                if use_free_apis:
                    print(f"   ⚠️  Azure OpenAI failed, trying free APIs...")
                    fallback_result = {
                        'status': 'partial',
                        'original_address': address_str,
                        'formatted_address': address_str,
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
                        'longitude': '',
                        'from_cache': False
                    }
                    
                    enhanced_fallback = self.fill_missing_components_with_free_apis(address_str, fallback_result)
                    
                    # Do NOT save failed attempts to database - let them be processed fresh each time
                    enhanced_fallback['address_id'] = None
                    print(f"   ⚠️  Not saving fallback data to database - will retry OpenAI next time")
                    
                    return enhanced_fallback
                
                return {
                    'status': 'error',
                    'reason': 'invalid_response',
                    'original_address': address_str,
                    'formatted_address': address_str,
                    'confidence': 'low',
                    'address_id': None,
                    'from_cache': False
                }
                
        except Exception as e:
            print(f"Error processing address '{address}': {str(e)}")
            return {
                'status': 'error',
                'reason': f'processing_error: {str(e)}',
                'original_address': str(address),
                'formatted_address': str(address),
                'confidence': 'low',
                'address_id': None,
                'from_cache': False
            }
    
    def standardize_addresses_batch(self, address_batch: List[str], start_index: int, target_country: str = None, use_free_apis: bool = True) -> List[Dict[str, Any]]:
        """
        Standardize a batch of addresses efficiently using batch API calls
        
        Args:
            address_batch: List of address strings to process
            start_index: Starting index for row numbering
            target_country: Target country for formatting
            use_free_apis: Whether to use free APIs for enhancement
            
        Returns:
            List of standardized address results
        """
        print(f"🚀 Processing batch of {len(address_batch)} addresses...")
        
        # Separate addresses into cached and non-cached
        cached_results = {}
        addresses_to_process = []
        addresses_to_process_mapping = {}  # Maps batch index to original index
        
        # Check database cache for each address
        for i, address in enumerate(address_batch):
            original_index = start_index + i
            
            if pd.isna(address) or not str(address).strip():
                cached_results[original_index] = {
                    'status': 'skipped',
                    'reason': 'empty_address',
                    'formatted_address': '',
                    'confidence': 'n/a',
                    'address_id': None,
                    'from_cache': False,
                    'input_index': i
                }
                continue
            
            address_str = str(address).strip()
            
            # Check database cache
            if self.db_service:
                existing_address = self.db_service.find_existing_address(address_str)
                if existing_address and existing_address.get('api_source') != 'fallback':
                    print(f"   ✅ Found cached address for row {original_index + 1}")
                    cached_results[original_index] = {
                        'status': 'success',
                        'original_address': address_str,
                        'formatted_address': existing_address['formatted_address'],
                        'street_number': existing_address['street_number'] or '',
                        'street_name': existing_address['street_name'] or '',
                        'street_type': existing_address['street_type'] or '',
                        'unit_type': existing_address['unit_type'] or '',
                        'unit_number': existing_address['unit_number'] or '',
                        'city': existing_address['city'] or '',
                        'state': existing_address['state'] or '',
                        'postal_code': existing_address['postal_code'] or '',
                        'country': existing_address['country'] or '',
                        'confidence': existing_address['confidence'] or '',
                        'issues': existing_address['issues'] or '',
                        'api_source': f"{existing_address['api_source']}_cached",
                        'latitude': str(existing_address['latitude']) if existing_address['latitude'] else '',
                        'longitude': str(existing_address['longitude']) if existing_address['longitude'] else '',
                        'address_id': existing_address['id'],
                        'from_cache': True,
                        'input_index': i
                    }
                    continue
            
            # Add to batch processing list
            batch_index = len(addresses_to_process)
            addresses_to_process.append(address_str)
            addresses_to_process_mapping[batch_index] = original_index
        
        # Process non-cached addresses in batch
        batch_results = []
        if addresses_to_process:
            print(f"   🤖 Processing {len(addresses_to_process)} addresses with AI batch processing...")
            try:
                batch_results = standardize_multiple_addresses(
                    addresses_to_process, 
                    target_country=target_country, 
                    use_batch=True
                )
            except Exception as e:
                print(f"   ❌ Batch processing failed, falling back to individual processing: {str(e)}")
                # Fallback to individual processing
                batch_results = []
                for i, address in enumerate(addresses_to_process):
                    try:
                        result = standardize_address(address, target_country)
                        result['input_index'] = i
                        result['original_address'] = address
                        batch_results.append(result)
                    except Exception as individual_error:
                        error_result = {
                            'error': str(individual_error),
                            'input_index': i,
                            'original_address': address,
                            'formatted_address': '',
                            'confidence': 'low',
                            'issues': ['processing_error']
                        }
                        batch_results.append(error_result)
        
        # Combine cached and batch processed results
        all_results = []
        for i in range(len(address_batch)):
            original_index = start_index + i
            
            # Check if we have a cached result
            if original_index in cached_results:
                all_results.append(cached_results[original_index])
            else:
                # Find the corresponding batch result
                batch_index = None
                for batch_idx, orig_idx in addresses_to_process_mapping.items():
                    if orig_idx == original_index:
                        batch_index = batch_idx
                        break
                
                if batch_index is not None and batch_index < len(batch_results):
                    result = batch_results[batch_index]
                    
                    # Convert to our expected format
                    enhanced_result = {
                        'status': 'success' if 'error' not in result else 'error',
                        'original_address': result.get('original_address', address_batch[i]),
                        'formatted_address': str(result.get('formatted_address', '')),
                        'street_number': str(result.get('street_number', '') or ''),
                        'street_name': str(result.get('street_name', '') or ''),
                        'street_type': str(result.get('street_type', '') or ''),
                        'unit_type': str(result.get('unit_type', '') or ''),
                        'unit_number': str(result.get('unit_number', '') or ''),
                        'city': str(result.get('city', '') or ''),
                        'state': str(result.get('state', '') or ''),
                        'postal_code': str(result.get('postal_code', '') or ''),
                        'country': str(result.get('country', '') or ''),
                        'confidence': result.get('confidence', 'unknown'),
                        'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                        'api_source': 'azure_openai_batch',
                        'latitude': '',
                        'longitude': '',
                        'from_cache': False,
                        'address_id': None
                    }
                    
                    # Try to enhance with free APIs if enabled
                    if use_free_apis and enhanced_result['status'] == 'success':
                        enhanced_result = self.fill_missing_components_with_free_apis(
                            enhanced_result['original_address'], 
                            enhanced_result
                        )
                    
                    # Save to database if successful
                    if self.db_service and enhanced_result['status'] == 'success':
                        try:
                            address_id = self.db_service.save_address(
                                enhanced_result.get('original_address', ''),
                                enhanced_result
                            )
                            enhanced_result['address_id'] = address_id
                        except Exception as db_error:
                            print(f"   ⚠️  Warning: Could not save to database: {str(db_error)}")
                    
                    all_results.append(enhanced_result)
                else:
                    # Fallback for missing results
                    all_results.append({
                        'status': 'error',
                        'reason': 'missing_result',
                        'original_address': str(address_batch[i]),
                        'formatted_address': str(address_batch[i]),
                        'confidence': 'low',
                        'from_cache': False,
                        'address_id': None
                    })
        
        print(f"✅ Batch completed: {len(all_results)} results")
        return all_results
    
    def process_csv_file(self, input_file: str, output_file: str = None, 
                        address_column: str = None, batch_size: int = 10, 
                        use_free_apis: bool = True, enable_batch_processing: bool = True) -> str:
        """
        Process a CSV file and standardize addresses using efficient batch processing
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            address_column: Specific column name containing addresses (optional)
            batch_size: Number of addresses to process in each batch (default: 10)
            use_free_apis: Whether to use free APIs to fill missing components
            enable_batch_processing: Whether to use batch processing for efficiency
        
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
            return self.process_regular_address_format(df, address_column, output_file, use_free_apis, enable_batch_processing)
    
    def process_site_address_format(self, df: pd.DataFrame, output_file: str = None, use_free_apis: bool = True) -> str:
        """Process CSV with site address column structure"""
        
        print(f"\n🏢 Processing Site Address Format")
        print("=" * 50)
        print("📋 Processing mode: ADD STANDARDIZED COLUMNS")
        print("   Original columns preserved + new standardized columns added")
        
        # Detect country column
        country_column = self.detect_country_column(df)
        
        # Add combined address column
        df['Combined_Address'] = df.apply(self.combine_site_address_fields, axis=1)
        
        # Add standardization result columns (including new database-related columns)
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
        df[f"{base_col_name}_address_id"] = ""  # New: Unique database ID
        df[f"{base_col_name}_from_cache"] = ""  # New: Whether from cache
        
        # Process each row
        total_rows = len(df)
        processed_count = 0
        success_count = 0
        error_count = 0
        cached_count = 0
        
        # Get batch size from config
        try:
            from app.config.address_config import PROMPT_CONFIG
            batch_size = PROMPT_CONFIG.get("batch_size", 10)
            enable_batch = PROMPT_CONFIG.get("enable_batch_processing", True)
        except ImportError:
            batch_size = 10
            enable_batch = True
        
        print(f"🚀 Processing {total_rows} addresses...")
        if enable_batch:
            print(f"   Using batch processing (batch size: {batch_size})")
        else:
            print(f"   Using individual processing")
        
        # Process in batches
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            # Extract addresses and countries for this batch
            batch_addresses = []
            batch_countries = []
            batch_indices = []
            
            for idx, (_, row) in enumerate(batch_df.iterrows()):
                combined_address = row['Combined_Address']
                batch_addresses.append(combined_address)
                
                # Get target country from column if available
                target_country = None
                if country_column and country_column in row:
                    target_country = str(row[country_column]).strip() if pd.notna(row[country_column]) else None
                batch_countries.append(target_country)
                batch_indices.append(batch_start + idx)
            
            # Process this batch
            if enable_batch and len(batch_addresses) > 1:
                print(f"   Processing batch {batch_start//batch_size + 1}: rows {batch_start+1}-{batch_end}")
                
                # Use the most common country in the batch, or None
                common_country = max(set(batch_countries), key=batch_countries.count) if any(batch_countries) else None
                
                batch_results = self.standardize_addresses_batch(
                    batch_addresses, 
                    batch_start, 
                    target_country=common_country, 
                    use_free_apis=use_free_apis
                )
            else:
                # Individual processing for small batches or when batch processing is disabled
                batch_results = []
                for i, address in enumerate(batch_addresses):
                    result = self.standardize_single_address(
                        address, 
                        batch_start + i, 
                        batch_countries[i], 
                        use_free_apis
                    )
                    batch_results.append(result)
            
            # Update DataFrame with batch results
            for i, result in enumerate(batch_results):
                df_index = batch_start + i
                
                # Update DataFrame with results
                df.at[df_index, f"{base_col_name}_formatted"] = result.get('formatted_address', '')
                df.at[df_index, f"{base_col_name}_street_number"] = result.get('street_number', '')
                df.at[df_index, f"{base_col_name}_street_name"] = result.get('street_name', '')
                df.at[df_index, f"{base_col_name}_street_type"] = result.get('street_type', '')
                df.at[df_index, f"{base_col_name}_unit_type"] = result.get('unit_type', '')
                df.at[df_index, f"{base_col_name}_unit_number"] = result.get('unit_number', '')
                df.at[df_index, f"{base_col_name}_city"] = result.get('city', '')
                df.at[df_index, f"{base_col_name}_state"] = result.get('state', '')
                df.at[df_index, f"{base_col_name}_postal_code"] = result.get('postal_code', '')
                df.at[df_index, f"{base_col_name}_country"] = result.get('country', '')
                df.at[df_index, f"{base_col_name}_confidence"] = result.get('confidence', '')
                df.at[df_index, f"{base_col_name}_issues"] = result.get('issues', '')
                df.at[df_index, f"{base_col_name}_status"] = result.get('status', '')
                df.at[df_index, f"{base_col_name}_api_source"] = result.get('api_source', '')
                df.at[df_index, f"{base_col_name}_latitude"] = result.get('latitude', '')
                df.at[df_index, f"{base_col_name}_longitude"] = result.get('longitude', '')
                df.at[df_index, f"{base_col_name}_address_id"] = result.get('address_id', '')
                df.at[df_index, f"{base_col_name}_from_cache"] = 'Yes' if result.get('from_cache', False) else 'No'
                
                processed_count += 1
                if result.get('status') == 'success':
                    success_count += 1
                else:
                    error_count += 1
                    
                if result.get('from_cache', False):
                    cached_count += 1
            
            # Progress indicator
            print(f"Progress: {processed_count}/{total_rows} ({processed_count/total_rows*100:.1f}%) - {cached_count} cached")
            
            # Small delay between batches to avoid overwhelming the API
            if not enable_batch:
                time.sleep(0.1)
        
        # Print enhanced summary with cache statistics
        print(f"\n📊 Processing Summary:")
        print(f"   Total processed: {processed_count}")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Cached addresses: {cached_count}/{processed_count} ({cached_count/processed_count*100:.1f}%)")
        print(f"   New addresses processed: {processed_count - cached_count}")
        
        return self.save_and_summarize_results(df, output_file, processed_count, success_count, error_count, ["Combined_Address"])
    
    def process_regular_address_format(self, df: pd.DataFrame, address_column: str = None, output_file: str = None, use_free_apis: bool = True) -> str:
        """Process CSV with regular address format"""
        
        # Detect country column
        country_column = self.detect_country_column(df)
        
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
            df[f"{base_col_name}_address_id"] = ""  # New: Unique database ID
            df[f"{base_col_name}_from_cache"] = ""  # New: Whether from cache
            
            # Process addresses in batches
            total_rows = len(df)
            processed_count = 0
            success_count = 0
            error_count = 0
            cached_count = 0
            
            for index, row in df.iterrows():
                address = row[addr_col]
                
                # Get target country from column if available
                target_country = None
                if country_column and country_column in row:
                    target_country = str(row[country_column]).strip() if pd.notna(row[country_column]) else None
                    
                result = self.standardize_single_address(address, index, target_country, use_free_apis)
                
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
                df.at[index, f"{base_col_name}_address_id"] = result.get('address_id', '')
                df.at[index, f"{base_col_name}_from_cache"] = 'Yes' if result.get('from_cache', False) else 'No'
                
                processed_count += 1
                if result.get('status') == 'success':
                    success_count += 1
                else:
                    error_count += 1
                    
                if result.get('from_cache', False):
                    cached_count += 1
                
                # Progress indicator
                if processed_count % 10 == 0:
                    print(f"Progress: {processed_count}/{total_rows} ({processed_count/total_rows*100:.1f}%) - {cached_count} cached")
                
                # Small delay to avoid overwhelming the API (only for non-cached)
                if not result.get('from_cache', False):
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
        
        # Extract basic components - handle None values safely
        street_number = (current_result.get('street_number') or '').strip() if current_result.get('street_number') else ''
        street_name = (current_result.get('street_name') or '').strip() if current_result.get('street_name') else ''
        street_type = (current_result.get('street_type') or '').strip() if current_result.get('street_type') else ''
        city = (current_result.get('city') or '').strip() if current_result.get('city') else ''
        state = (current_result.get('state') or '').strip() if current_result.get('state') else ''
        postal_code = (current_result.get('postal_code') or '').strip() if current_result.get('postal_code') else ''
        country = (current_result.get('country') or '').strip() if current_result.get('country') else ''
        
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
    """Enhanced command line interface supporting both CSV files and direct address input"""
    parser = argparse.ArgumentParser(
        description='AddressIQ: Standardize addresses from CSV files or direct input',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process CSV file
  python csv_address_processor.py addresses.csv
  
  # Process single address
  python csv_address_processor.py --address "123 Main St, NYC, NY"
  
  # Process multiple addresses
  python csv_address_processor.py --addresses "123 Main St, NYC" "456 Oak Ave, LA"
  
  # With country specification
  python csv_address_processor.py --address "123 High St, London" --country "UK"
  
  # Different output formats
  python csv_address_processor.py --address "123 Main St" --format formatted
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'input_file', 
        nargs='?', 
        help='CSV file containing addresses to process'
    )
    input_group.add_argument(
        '--address', '-a',
        help='Single address to process'
    )
    input_group.add_argument(
        '--addresses', '-A',
        nargs='+',
        help='Multiple addresses to process'
    )
    
    # Options for CSV processing
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-c', '--column', help='Specific address column name (for CSV)')
    parser.add_argument('-b', '--batch-size', type=int, default=5, help='Batch size for processing (default: 5)')
    parser.add_argument('--no-free-apis', action='store_true', help='Disable free API enhancement')
    
    # Options for direct address processing
    parser.add_argument(
        '--country',
        help='Target country for formatting (e.g., USA, UK, India)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'formatted', 'detailed'],
        default='json',
        help='Output format for direct address processing (default: json)'
    )
    
    # Utility options
    parser.add_argument('--test-apis', action='store_true', help='Test free APIs and exit')
    parser.add_argument('--db-stats', action='store_true', help='Show database statistics and exit')
    
    args = parser.parse_args()
    
    # Create processor instance
    processor = CSVAddressProcessor()
    
    # Show database stats if requested
    if args.db_stats:
        if processor.db_service:
            stats = processor.db_service.get_database_stats()
            print("📊 AddressIQ Azure SQL Database Statistics")
            print("=" * 50)
            print(f"Server: dev-server-sqldb.database.windows.net")
            print(f"Total unique addresses: {stats['total_unique_addresses']:,}")
            print(f"Total address lookups: {stats['total_address_lookups']:,}")
            print(f"Addresses reused: {stats['reused_addresses']:,}")
            print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
            print(f"API calls saved: {stats['total_address_lookups'] - stats['total_unique_addresses']:,}")
        else:
            print("❌ Database service not available")
        return
    
    # Test APIs if requested
    if args.test_apis:
        processor.test_free_apis()
        return
    
    # Process based on input type
    if args.input_file:
        # CSV file processing (existing functionality)
        print(f"📁 Processing CSV file: {args.input_file}")
        try:
            output_file = processor.process_csv_file(
                input_file=args.input_file,
                output_file=args.output,
                address_column=args.column,
                batch_size=args.batch_size,
                use_free_apis=not args.no_free_apis
            )
            print(f"\n✅ Processing completed successfully!")
            print(f"📁 Output saved to: {output_file}")
            
            # Show final database stats
            if processor.db_service:
                final_stats = processor.db_service.get_database_stats()
                print(f"\n📊 Final Azure SQL Database Stats:")
                print(f"   Total unique addresses: {final_stats['total_unique_addresses']:,}")
                print(f"   Cache hit rate: {final_stats['cache_hit_rate']:.1f}%")
                
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            sys.exit(1)
            
    elif args.address:
        # Single address processing
        print(f"🏠 Processing single address")
        result = processor.process_single_address_input(
            args.address, 
            args.country, 
            args.format
        )
        
        if args.output:
            # Save to JSON file
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Result saved to: {args.output}")
        else:
            # Print to console
            print(f"\n📋 Result:")
            if args.format == 'formatted':
                print(f"   Original: {result.get('original_address', 'N/A')}")
                print(f"   Formatted: {result.get('formatted_address', 'N/A')}")
                print(f"   Confidence: {result.get('confidence', 'N/A')}")
                print(f"   From cache: {result.get('from_cache', False)}")
                print(f"   Status: {result.get('status', 'N/A')}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
    elif args.addresses:
        # Multiple addresses processing
        print(f"🏠 Processing {len(args.addresses)} addresses")
        results = processor.process_multiple_addresses_input(
            args.addresses,
            args.country,
            args.format
        )
        
        if args.output:
            # Save to JSON file
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Results saved to: {args.output}")
        else:
            # Print to console
            print(f"\n📋 Results:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Address {i} ---")
                if args.format == 'formatted':
                    print(f"   Original: {result.get('original_address', 'N/A')}")
                    print(f"   Formatted: {result.get('formatted_address', 'N/A')}")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}")
                    print(f"   From cache: {result.get('from_cache', False)}")
                    print(f"   Status: {result.get('status', 'N/A')}")
                else:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        # No input provided, show help
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
