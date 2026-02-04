#!/usr/bin/env python3
"""
Enhanced CSV Address Processor for AddressIQ with Inbound/Outbound Directory Management
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
import shutil
import glob
import re

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.azure_openai import standardize_address, standardize_multiple_addresses, compare_multiple_addresses, read_csv_with_encoding_detection

# Import address splitter
try:
    from address_splitter import AddressSplitter
    ADDRESS_SPLITTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Address splitter not available: {str(e)}")
    ADDRESS_SPLITTER_AVAILABLE = False

# Database caching removed - all addresses processed directly via API

class CSVAddressProcessor:
    """
    A comprehensive address processor that can:
    1. Read CSV files from inbound directory
    2. Process single addresses directly
    3. Process multiple addresses from input
    4. Detect address columns automatically
    5. Standardize addresses using Azure OpenAI
    6. Add detailed standardization results
    7. Fill missing address components using free APIs
    8. Save enhanced CSV to outbound directory
    9. Manage inbound/outbound directories automatically
    """
    
    def __init__(self, base_directory: str = None):
        # Set up directory structure
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.inbound_dir = self.base_directory / "inbound"
        self.outbound_dir = self.base_directory / "outbound"
        self.archive_dir = self.base_directory / "archive"
        
        # Create directories if they don't exist
        self.setup_directories()
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
        
        # Database services removed - no caching
        self.db_service = None
        self.db_connector = None
        
        # Initialize address splitter
        if ADDRESS_SPLITTER_AVAILABLE:
            try:
                # Initialize with rule-based by default (can be changed via parameter)
                self.address_splitter = AddressSplitter(use_gpt=False)
                print("✅ Address splitter initialized successfully (rule-based mode)")
            except Exception as e:
                print(f"⚠️  Warning: Address splitter initialization failed: {str(e)}")
                self.address_splitter = None
        else:
            self.address_splitter = None
        
    def setup_directories(self):
            self.db_service = None
            print("⚠️  Running without database caching")
    
    def setup_directories(self):
        """Create and setup the directory structure"""
        print("📁 Setting up directory structure...")
        
        # Create directories
        self.inbound_dir.mkdir(exist_ok=True)
        self.outbound_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        
        print(f"   📥 Inbound directory: {self.inbound_dir}")
        print(f"   📤 Outbound directory: {self.outbound_dir}")
        print(f"   📦 Archive directory: {self.archive_dir}")
        
        # Show directory status
        inbound_files = list(self.inbound_dir.glob("*.csv"))
        outbound_files = list(self.outbound_dir.glob("*.csv"))
        
        print(f"   📊 Inbound files: {len(inbound_files)}")
        print(f"   📊 Outbound files: {len(outbound_files)}")
        
        if inbound_files:
            print(f"   📋 Files in inbound: {[f.name for f in inbound_files]}")
    
    def clean_outbound_directory(self):
        """Clean the outbound directory before processing"""
        print("🧹 Cleaning outbound directory...")
        
        outbound_files = list(self.outbound_dir.glob("*"))
        if outbound_files:
            for file_path in outbound_files:
                try:
                    if file_path.is_file():
                        file_path.unlink()  # Delete file
                        print(f"   🗑️  Deleted: {file_path.name}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)  # Delete directory
                        print(f"   🗑️  Deleted directory: {file_path.name}")
                except Exception as e:
                    print(f"   ⚠️  Could not delete {file_path.name}: {e}")
            
            print(f"✅ Cleaned {len(outbound_files)} items from outbound directory")
        else:
            print("✅ Outbound directory already clean")
    
    def archive_inbound_files(self, processed_files: List[Path]):
        """Move processed files from inbound to archive directory"""
        print("📦 Archiving processed files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_count = 0
        
        for file_path in processed_files:
            try:
                # Create archive filename with timestamp
                archive_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                archive_path = self.archive_dir / archive_filename
                
                # Move file to archive
                shutil.move(str(file_path), str(archive_path))
                print(f"   📦 Archived: {file_path.name} → {archive_filename}")
                archived_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Could not archive {file_path.name}: {e}")
        
        print(f"✅ Archived {archived_count} files")
    
    def archive_single_inbound_file(self, input_file_path: str) -> bool:
        """Archive a single file if it's from the inbound directory"""
        input_path = Path(input_file_path).resolve()  # Convert to absolute path
        
        # Check if file is from inbound directory
        if input_path.parent == self.inbound_dir:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_filename = f"{input_path.stem}_{timestamp}{input_path.suffix}"
                archive_path = self.archive_dir / archive_filename
                
                # Move file to archive
                shutil.move(str(input_path), str(archive_path))
                print(f"📦 Archived inbound file: {input_path.name} → {archive_filename}")
                return True
                
            except Exception as e:
                print(f"⚠️  Could not archive inbound file {input_path.name}: {e}")
                return False
        
        return False  # File was not from inbound directory
    
    def get_inbound_files(self) -> List[Path]:
        """Get all CSV files from inbound directory"""
        csv_files = list(self.inbound_dir.glob("*.csv"))
        xlsx_files = list(self.inbound_dir.glob("*.xlsx"))  # Also support Excel files
        
        all_files = csv_files + xlsx_files
        
        if all_files:
            print(f"📥 Found {len(all_files)} files in inbound directory:")
            for file_path in all_files:
                print(f"   📄 {file_path.name}")
        else:
            print("📥 No CSV/Excel files found in inbound directory")
        
        return all_files
    
    def process_all_inbound_files(self, batch_size: int = 10, use_free_apis: bool = False, enable_split: bool = False, use_gpt_split: bool = False):
        """Process all files in the inbound directory"""
        print("🚀 Starting batch processing of inbound files...")
        print("=" * 60)
        
        # Clean outbound directory first
        self.clean_outbound_directory()
        
        # Get all inbound files
        inbound_files = self.get_inbound_files()
        
        if not inbound_files:
            print("❌ No files to process in inbound directory")
            return
        
        processed_files = []
        total_success = 0
        total_errors = 0
        
        for file_path in inbound_files:
            try:
                print(f"\n🔄 Processing: {file_path.name}")
                print("-" * 40)
                
                # Generate output filename in outbound directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{file_path.stem}_processed_{timestamp}.csv"
                output_path = self.outbound_dir / output_filename
                
                # Process the file
                result_path = self.process_csv_file(
                    input_file=str(file_path),
                    output_file=str(output_path),
                    batch_size=batch_size,
                    use_free_apis=use_free_apis,
                    enable_split=enable_split,
                    use_gpt_split=use_gpt_split
                )
                
                if result_path:
                    print(f"✅ Successfully processed: {file_path.name}")
                    print(f"📤 Output saved to: {output_filename}")
                    processed_files.append(file_path)
                    total_success += 1
                else:
                    print(f"❌ Failed to process: {file_path.name}")
                    total_errors += 1
                    
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {str(e)}")
                total_errors += 1
        
        # Archive processed files
        if processed_files:
            self.archive_inbound_files(processed_files)
        
        # Final summary
        print(f"\n{'='*60}")
        print("BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Files processed successfully: {total_success}")
        print(f"Files with errors: {total_errors}")
        print(f"Total files: {len(inbound_files)}")
        print(f"📤 Output files in: {self.outbound_dir}")
        print(f"📦 Processed files archived to: {self.archive_dir}")
    
    def process_all_inbound_comparison_files(self, batch_size: int = 5):
        """Process all comparison files in the inbound directory"""
        print("🚀 Starting batch processing of inbound comparison files...")
        print("=" * 60)
        
        # Clean outbound directory first
        self.clean_outbound_directory()
        
        # Get all inbound files
        inbound_files = self.get_inbound_files()
        
        if not inbound_files:
            print("❌ No files to process in inbound directory")
            return
        
        processed_files = []
        total_success = 0
        total_errors = 0
        
        for file_path in inbound_files:
            try:
                print(f"\n🔄 Processing comparison file: {file_path.name}")
                print("-" * 40)
                
                # Process the comparison file
                output_path = self.process_csv_comparison_file(
                    input_file=str(file_path),
                    batch_size=batch_size
                )
                
                if output_path:
                    processed_files.append(file_path)
                    total_success += 1
                    print(f"✅ Successfully processed: {file_path.name}")
                    print(f"📁 Output saved to: {Path(output_path).name}")
                else:
                    total_errors += 1
                    print(f"❌ Failed to process: {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {str(e)}")
                total_errors += 1
                continue
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 BATCH COMPARISON PROCESSING SUMMARY")
        print("=" * 60)
        print(f"📁 Files found: {len(inbound_files)}")
        print(f"✅ Successfully processed: {total_success}")
        print(f"❌ Errors: {total_errors}")
        
        if processed_files:
            print(f"📦 Processed files archived from inbound directory")
        
        if total_errors == 0 and total_success > 0:
            print("🎉 All comparison files processed successfully!")
        elif total_success > 0:
            print("⚠️  Some files processed with errors - check logs above")
        else:
            print("❌ No files were processed successfully")
    
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
        
        # Process with AI (no caching)
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
                    'building_name': result.get('building_name', '') or '',
                    'floor_number': result.get('floor_number', '') or '',
                    'city': result.get('city', '') or '',
                    'state': result.get('state', '') or '',
                    'county': result.get('county', '') or '',
                    'postal_code': result.get('postal_code', '') or '',
                    'country': result.get('country', '') or '',
                    'country_code': result.get('country_code', '') or '',
                    'district': result.get('district', '') or '',
                    'region': result.get('region', '') or '',
                    'suburb': result.get('suburb', '') or '',
                    'locality': result.get('locality', '') or '',
                    'sublocality': result.get('sublocality', '') or '',
                    'canton': result.get('canton', '') or '',
                    'prefecture': result.get('prefecture', '') or '',
                    'oblast': result.get('oblast', '') or '',
                    'confidence': result.get('confidence', 'medium') or 'medium',
                    'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                    'api_source': 'azure_openai',
                    'address_type': result.get('address_type', '') or '',
                    'po_box': result.get('po_box', '') or '',
                    'delivery_instructions': result.get('delivery_instructions', '') or '',
                    'mail_route': result.get('mail_route', '') or '',
                    'latitude': '',
                    'longitude': '',
                    'from_cache': False
                }
                
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
        
        # Process all addresses via API (no caching)
        print(f"🤖 Processing {len(addresses)} addresses via API")
        
        # Process addresses in batches
        if addresses:
            try:
                ai_results = standardize_multiple_addresses(addresses, use_batch=True)
                
                for i, address in enumerate(addresses):
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
                        
                        # Format and add result
                        results.append(self._format_output(result, output_format))
                    else:
                        # Fallback for missing results
                        results.append(self._format_output({
                            'status': 'failed',
                            'error': 'No result from AI',
                            'original_address': address,
                            'from_cache': False
                        }, output_format))
                        
            except Exception as e:
                print(f"❌ Error in batch processing: {e}")
                # Fallback to individual processing
                for original_index, address in new_addresses:
                    results[original_index] = self.process_single_address_input(address, country, output_format)
        
        return results

    def process_database_input(self, 
                              db_type: str,
                              connection_params: Dict[str, Any],
                              query: str = None,
                              table_name: str = None,
                              address_columns: List[str] = None,
                              limit: int = None,
                              batch_size: int = 10,
                              use_free_apis: bool = False) -> Dict[str, Any]:
        """
        Process addresses directly from database input
        
        Args:
            db_type: Database type (sqlserver, mysql, postgresql, etc.)
            connection_params: Database connection parameters
            query: Custom SQL query (optional)
            table_name: Table name to extract from (if no query provided)
            address_columns: List of columns containing address data
            limit: Limit number of records to process
            batch_size: Batch size for processing
            use_free_apis: Whether to use free APIs for enhancement
            
        Returns:
            Dict with processing results and file paths
        """
        
        if not DATABASE_CONNECTOR_AVAILABLE or not self.db_connector:
            return {
                'success': False,
                'error': 'Database connector service not available'
            }
        
        print(f"\n🗃️ Processing addresses from {db_type} database")
        print("=" * 60)
        
        # Step 1: Extract data from database to CSV
        print(f"📥 Extracting data from database...")
        
        extraction_result = self.db_connector.extract_data_to_csv(
            db_type=db_type,
            connection_params=connection_params,
            query=query,
            table_name=table_name,
            address_columns=address_columns,
            limit=limit
        )
        
        if not extraction_result['success']:
            return {
                'success': False,
                'error': f"Database extraction failed: {extraction_result['error']}"
            }
        
        csv_file_path = extraction_result['csv_file_path']
        
        print(f"✅ Successfully extracted {extraction_result['records_extracted']} records")
        print(f"📁 Saved to: {csv_file_path}")
        print(f"🔍 Detected address columns: {extraction_result['detected_address_columns']}")
        
        # Step 2: Process the extracted CSV file
        print(f"\n🏠 Processing extracted addresses...")
        
        try:
            # Determine which address column to process
            primary_address_column = None
            if address_columns and len(address_columns) > 0:
                # Use the first specified address column as primary
                primary_address_column = address_columns[0]
                print(f"📍 Using primary address column: {primary_address_column}")
            elif extraction_result['detected_address_columns']:
                # Use the first detected address column as primary
                primary_address_column = extraction_result['detected_address_columns'][0]
                print(f"📍 Using detected primary address column: {primary_address_column}")
            
            # Process the CSV file using existing functionality
            processing_result = self.process_csv_file(
                input_file=csv_file_path,
                address_column=primary_address_column,  # Specify the primary column
                batch_size=batch_size,
                use_free_apis=use_free_apis
            )
            
            return {
                'success': True,
                'database_extraction': extraction_result,
                'address_processing': processing_result,
                'input_csv_path': csv_file_path,
                'output_csv_path': processing_result.get('output_file') if isinstance(processing_result, dict) else processing_result,
                'records_processed': extraction_result['records_extracted'],
                'database_type': db_type,
                'processing_summary': processing_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Address processing failed: {str(e)}",
                'database_extraction': extraction_result,
                'input_csv_path': csv_file_path
            }
    
    def get_supported_databases(self) -> List[str]:
        """Get list of supported database types"""
        if DATABASE_CONNECTOR_AVAILABLE and self.db_connector:
            return self.db_connector.get_supported_databases()
        else:
            return []
    
    def test_database_connection(self, db_type: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection before processing"""
        if not DATABASE_CONNECTOR_AVAILABLE or not self.db_connector:
            return {
                'success': False,
                'error': 'Database connector service not available'
            }
        
        return self.db_connector.test_connection(db_type, connection_params)
    
    def validate_database_params(self, db_type: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate database connection parameters"""
        if not DATABASE_CONNECTOR_AVAILABLE or not self.db_connector:
            return {
                'valid': False,
                'errors': ['Database connector service not available']
            }
        
        return self.db_connector.validate_connection_params(db_type, connection_params)
    
    def preview_database_table(self, db_type: str, connection_params: Dict[str, Any], table_name: str = None) -> Dict[str, Any]:
        """Preview database table structure and sample data"""
        if not DATABASE_CONNECTOR_AVAILABLE or not self.db_connector:
            return {
                'success': False,
                'error': 'Database connector service not available'
            }
        
        return self.db_connector.preview_table_structure(db_type, connection_params, table_name)

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
    
    def detect_separated_address_components(self, df: pd.DataFrame) -> dict:
        """Detect if address components are in separate columns (like Address Line 1, City, Postcode, etc.)"""
        columns_lower = {col.lower().replace(' ', '_').replace('-', '_'): col for col in df.columns}
        
        # Define patterns for different address components - support multiple address lines
        address_line_patterns = {
            'address_line_1': ['address_line_1', 'address_line1', 'street_address', 'address_1', 'address1', 'street', 'address', 'line_1', 'line1'],
            'address_line_2': ['address_line_2', 'address_line2', 'address_2', 'address2', 'line_2', 'line2', 'apartment', 'apt', 'unit', 'suite'],
            'address_line_3': ['address_line_3', 'address_line3', 'address_3', 'address3', 'line_3', 'line3', 'additional', 'care_of'],
            'address_line_4': ['address_line_4', 'address_line4', 'address_4', 'address4', 'line_4', 'line4'],
            'address_line_5': ['address_line_5', 'address_line5', 'address_5', 'address5', 'line_5', 'line5']
        }
        
        city_patterns = ['city', 'town', 'locality']
        state_patterns = ['state', 'province', 'region', 'county'] 
        postal_patterns = ['postcode', 'postal_code', 'zip_code', 'zip', 'postalcode']
        country_patterns = ['country', 'nation']
        
        detected_components = {}
        
        # Find all address line columns
        for line_type, patterns in address_line_patterns.items():
            for pattern in patterns:
                for col_key, col_name in columns_lower.items():
                    if pattern in col_key:
                        detected_components[line_type] = col_name
                        break
                if line_type in detected_components:
                    break
        
        # Find city columns
        for pattern in city_patterns:
            for col_key, col_name in columns_lower.items():
                if col_key == pattern:  # Exact match for city
                    detected_components['city'] = col_name
                    break
            if 'city' in detected_components:
                break
        
        # Find state/county columns
        for pattern in state_patterns:
            for col_key, col_name in columns_lower.items():
                if col_key == pattern:
                    detected_components['state'] = col_name
                    break
            if 'state' in detected_components:
                break
        
        # Find postal code columns
        for pattern in postal_patterns:
            for col_key, col_name in columns_lower.items():
                if pattern in col_key:
                    detected_components['postal_code'] = col_name
                    break
            if 'postal_code' in detected_components:
                break
        
        # Find country columns
        for pattern in country_patterns:
            for col_key, col_name in columns_lower.items():
                if col_key == pattern:
                    detected_components['country'] = col_name
                    break
        
        return detected_components
    
    def combine_separated_address_components(self, row: pd.Series, component_mapping: dict) -> str:
        """Combine separated address components into a single address string"""
        address_parts = []
        
        # Add all address lines in order (1, 2, 3, 4, 5)
        for line_num in range(1, 6):
            line_key = f'address_line_{line_num}'
            if line_key in component_mapping:
                addr_line = str(row[component_mapping[line_key]]).strip()
                if addr_line and addr_line.lower() != 'nan':
                    address_parts.append(addr_line)
        
        # Add city
        if 'city' in component_mapping:
            city = str(row[component_mapping['city']]).strip()
            if city and city.lower() != 'nan':
                address_parts.append(city)
        
        # Add state/county
        if 'state' in component_mapping:
            state = str(row[component_mapping['state']]).strip()
            if state and state.lower() != 'nan':
                address_parts.append(state)
        
        # Add postal code
        if 'postal_code' in component_mapping:
            postal = str(row[component_mapping['postal_code']]).strip()
            if postal and postal.lower() != 'nan':
                address_parts.append(postal)
        
        # Add country
        if 'country' in component_mapping:
            country = str(row[component_mapping['country']]).strip()
            if country and country.lower() != 'nan':
                address_parts.append(country)
        
        return ', '.join(address_parts)
    
    def detect_site_address_columns(self, df: pd.DataFrame) -> bool:
        """Check if the DataFrame has the specific site address column structure"""
        available_columns = [col.lower() for col in df.columns.tolist()]
        
        # Check for various site address column patterns
        address_line_patterns = [
            'site_address_line1', 'site_address_line2', 'site_address_line3', 'site_address_line4',
            'site_address_1', 'site_address_2', 'site_address_3', 'site_address_4',
            'address_line1', 'address_line2', 'address_line3'
        ]
        
        city_patterns = ['site_city', 'city']
        state_patterns = ['site_state', 'state']
        postcode_patterns = ['site_postcode', 'postcode', 'postal_code', 'zip_code']
        country_patterns = ['site_country', 'country']
        
        # Check if we have at least one address line and some geographical components
        has_address_line = any(pattern in available_columns for pattern in address_line_patterns)
        has_city = any(pattern in available_columns for pattern in city_patterns)
        has_state = any(pattern in available_columns for pattern in state_patterns)
        has_postcode = any(pattern in available_columns for pattern in postcode_patterns)
        has_country = any(pattern in available_columns for pattern in country_patterns)
        
        # Count how many geographic components we have
        geo_components = sum([has_city, has_state, has_postcode, has_country])
        
        if has_address_line and geo_components >= 2:
            print(f"✅ Detected site address column structure!")
            print(f"   Address lines: {has_address_line}")
            print(f"   Geographic components found: {geo_components}/4 (city: {has_city}, state: {has_state}, postcode: {has_postcode}, country: {has_country})")
            return True
        else:
            print(f"❌ Site address structure not detected")
            print(f"   Address lines: {has_address_line}")
            print(f"   Geographic components: {geo_components}/4 (need at least 2)")
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
    
    def combine_address_columns(self, row: pd.Series, column_names: List[str]) -> str:
        """Combine specified columns into a single address string - column name independent"""
        address_parts = []
        
        for col_name in column_names:
            if col_name in row and pd.notna(row[col_name]):
                value = str(row[col_name]).strip()
                # Skip empty values, NULL strings, and common placeholder values
                if value and value.upper() not in ['NULL', 'N/A', 'NA', '', 'NONE']:
                    address_parts.append(value)
        
        # Join all parts with commas and return
        combined_address = ', '.join(address_parts)
        return combined_address if combined_address.strip() else ""

    def combine_site_address_fields(self, row: pd.Series) -> str:
        """Combine separate site address fields into a single address string"""
        address_parts = []
        
        # Add address lines - handle multiple naming conventions
        address_line_columns = [
            # Canonical new format
            'Site_Address_1', 'Site_Address_2', 'Site_Address_3', 'Site_Address_4',
            # Legacy formats (accepted for backward compatibility)
            'Site_Address_Line1', 'Site_Address_line2', 'Site_Address_line3', 'Site_Address_Line4',
            # Generic format
            'address_line1', 'address_line2', 'address_line3', 'address_line4'
        ]
        
        for addr_col in address_line_columns:
            if addr_col in row and pd.notna(row[addr_col]) and str(row[addr_col]).strip() and str(row[addr_col]).strip().upper() != 'NULL':
                address_parts.append(str(row[addr_col]).strip())
        
        # Add city - handle multiple naming conventions
        city_columns = ['Site_City', 'City', 'city']  # Canonical + generic
        for city_col in city_columns:
            if city_col in row and pd.notna(row[city_col]) and str(row[city_col]).strip() and str(row[city_col]).strip().upper() != 'NULL':
                address_parts.append(str(row[city_col]).strip())
                break  # Only add one city column
            
        # Add state - handle multiple naming conventions
        state_columns = ['Site_State', 'State', 'state']  # Canonical + generic
        for state_col in state_columns:
            if state_col in row and pd.notna(row[state_col]) and str(row[state_col]).strip() and str(row[state_col]).strip().upper() != 'NULL':
                address_parts.append(str(row[state_col]).strip())
                break  # Only add one state column
            
        # Add postal code - handle multiple naming conventions
        postcode_columns = ['Site_Postcode', 'Site_PostCode', 'PostCode', 'postal_code', 'zip_code']  # Canonical first
        for postcode_col in postcode_columns:
            if postcode_col in row and pd.notna(row[postcode_col]) and str(row[postcode_col]).strip() and str(row[postcode_col]).strip().upper() != 'NULL':
                address_parts.append(str(row[postcode_col]).strip())
                break  # Only add one postcode column
        
        # Add country - handle multiple naming conventions
        country_columns = ['Site_Country', 'Site_country', 'Country', 'country']  # Canonical first
        for country_col in country_columns:
            if country_col in row and pd.notna(row[country_col]) and str(row[country_col]).strip() and str(row[country_col]).strip().upper() != 'NULL':
                address_parts.append(str(row[country_col]).strip())
                break  # Only add one country column
        
        # Join all parts with commas
        combined_address = ', '.join(address_parts)
        return combined_address if combined_address.strip() else ""
    
    def standardize_single_address(self, address: str, row_index: int, target_country: str = None, use_free_apis: bool = False) -> Dict[str, Any]:
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
            
            
            # NEW: Try geocoding FIRST if enabled (for incomplete addresses)
            geocoding_result = None
            if use_free_apis:
                # Check if address looks incomplete (missing city, state, or zip)
                address_lower = address_str.lower()
                has_state_abbr = any(f' {state.lower()} ' in f' {address_lower} ' or f' {state.lower()},' in f' {address_lower} ' 
                                    for state in ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 
                                                 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
                                                 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
                                                 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
                                                 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy'])
                has_zip = any(c.isdigit() for c in address_str) and len([c for c in address_str if c.isdigit()]) >= 5
                has_comma = ',' in address_str
                
                # If address appears incomplete, try geocoding first
                if not (has_state_abbr and has_zip and has_comma):
                    print(f"   🌐 Address appears incomplete, trying geocoding first...")
                    
                    if self.free_apis['nominatim']['enabled']:
                        time.sleep(self.free_apis['nominatim']['rate_limit'])
                        geocoding_result = self.geocode_with_nominatim(address_str)
                        
                        if geocoding_result.get('success'):
                            print(f"   ✅ Geocoding found complete address: {geocoding_result.get('formatted_address', '')[:80]}")
                            # Use geocoded address as the enriched input for AI standardization
                            enriched_address = geocoding_result.get('formatted_address', address_str)
                        else:
                            print(f"   ⚠️  Geocoding failed, will process with AI only")
                            enriched_address = address_str
                    else:
                        enriched_address = address_str
                else:
                    enriched_address = address_str
            else:
                enriched_address = address_str
            
            # Process with AI model (using enriched address if geocoding succeeded)
            print(f"   🤖 Processing with AI model...")
            if target_country:
                print(f"   🌍 Using country-specific formatting for: {target_country}")
            result = standardize_address(enriched_address if geocoding_result and geocoding_result.get('success') else address_str, target_country)
            
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
                    'country_code': str(result.get('country_code', '') or ''),
                    'district': str(result.get('district', '') or ''),
                    'region': str(result.get('region', '') or ''),
                    'suburb': str(result.get('suburb', '') or ''),
                    'locality': str(result.get('locality', '') or ''),
                    'sublocality': str(result.get('sublocality', '') or ''),
                    'canton': str(result.get('canton', '') or ''),
                    'prefecture': str(result.get('prefecture', '') or ''),
                    'oblast': str(result.get('oblast', '') or ''),
                    'confidence': result.get('confidence', 'unknown'),
                    'issues': ', '.join(result.get('issues', [])) if result.get('issues') else '',
                    'api_source': 'geocoding_then_azure_openai' if (geocoding_result and geocoding_result.get('success')) else 'azure_openai',
                    'latitude': '',
                    'longitude': '',
                    'from_cache': False
                }
                
                # If geocoding provided coordinates, use them
                if geocoding_result and geocoding_result.get('success'):
                    enhanced_result['latitude'] = geocoding_result.get('latitude', '')
                    enhanced_result['longitude'] = geocoding_result.get('longitude', '')
                
                # Still try to enhance with free APIs if coordinates missing or other components missing
                if use_free_apis:
                    enhanced_result = self.fill_missing_components_with_free_apis(address_str, enhanced_result)
                
                # No database saving
                enhanced_result['address_id'] = None
                
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
    
    def standardize_addresses_batch(self, address_batch: List[str], start_index: int, target_country: str = None, use_free_apis: bool = False) -> List[Dict[str, Any]]:
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
        
        # Process all addresses (no caching)
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
            
            # Add to batch processing list (no cache lookup)
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
                        'country_code': str(result.get('country_code', '') or ''),
                        'district': str(result.get('district', '') or ''),
                        'region': str(result.get('region', '') or ''),
                        'suburb': str(result.get('suburb', '') or ''),
                        'locality': str(result.get('locality', '') or ''),
                        'sublocality': str(result.get('sublocality', '') or ''),
                        'canton': str(result.get('canton', '') or ''),
                        'prefecture': str(result.get('prefecture', '') or ''),
                        'oblast': str(result.get('oblast', '') or ''),
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
        
        # No database saving
        print(f"✅ Batch completed: {len(all_results)} results")
        return all_results
    
    def apply_address_splitting(self, df: pd.DataFrame, address_columns: List[str]) -> pd.DataFrame:
        """
        Apply address splitting to the dataframe. Creates new rows for split addresses.
        
        Args:
            df: Input dataframe
            address_columns: List of address column names to check for splitting
            
        Returns:
            Modified dataframe with split addresses as new rows
        """
        print(f"\n✂️  Analyzing addresses for splitting...")
        
        # Create a list to hold all rows (original and split)
        new_rows = []
        split_count = 0
        no_split_count = 0
        
        # Detect if there's an Address2 column
        address2_col = None
        for col in df.columns:
            if col.lower() in ['address2', 'address_2', 'site_address_2', 'address_line_2']:
                address2_col = col
                break
        
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            
            # Get the primary address column
            primary_addr_col = address_columns[0]
            address1 = str(row[primary_addr_col]) if pd.notna(row[primary_addr_col]) else ""
            address2 = str(row[address2_col]) if address2_col and pd.notna(row[address2_col]) else None
            
            # Skip empty addresses
            if not address1.strip():
                new_rows.append(row_dict)
                no_split_count += 1
                continue
            
            # Analyze and split if needed
            # When using GPT-based splitting, it will intelligently determine
            # if Address2 contains additional addresses or just building/suite info
            split_result = self.address_splitter.analyze_and_split(address1, address2)
            
            if split_result['should_split'] and split_result['split_count'] > 1:
                # Address was split - create multiple rows
                split_count += 1
                print(f"   Row {index + 1}: Split into {split_result['split_count']} addresses")
                print(f"      Reason: {split_result['split_reason']}")
                
                # Add metadata columns if they don't exist
                if 'Split_Indicator' not in row_dict:
                    row_dict['Split_Indicator'] = ''
                if 'Split_From_Row' not in row_dict:
                    row_dict['Split_From_Row'] = ''
                if 'Split_Address_Number' not in row_dict:
                    row_dict['Split_Address_Number'] = ''
                
                # Create a new row for each split address
                for split_idx, split_addr in enumerate(split_result['addresses'], 1):
                    new_row = row_dict.copy()
                    new_row[primary_addr_col] = split_addr
                    new_row['Split_Indicator'] = 'Yes'
                    new_row['Split_From_Row'] = index + 1
                    new_row['Split_Address_Number'] = f"{split_idx} of {split_result['split_count']}"
                    
                    # Clear address2 if it was used in splitting
                    if address2_col and address2:
                        new_row[address2_col] = ''
                    
                    new_rows.append(new_row)
            else:
                # No split - keep original row
                no_split_count += 1
                
                # Add metadata columns
                if 'Split_Indicator' not in row_dict:
                    row_dict['Split_Indicator'] = 'No'
                if 'Split_From_Row' not in row_dict:
                    row_dict['Split_From_Row'] = ''
                if 'Split_Address_Number' not in row_dict:
                    row_dict['Split_Address_Number'] = ''
                else:
                    row_dict['Split_Indicator'] = 'No'
                
                new_rows.append(row_dict)
        
        # Create new dataframe from all rows
        new_df = pd.DataFrame(new_rows)
        
        print(f"\n📊 Split Analysis Summary:")
        print(f"   Original rows: {len(df)}")
        print(f"   Rows with splits: {split_count}")
        print(f"   Rows without splits: {no_split_count}")
        print(f"   Final rows: {len(new_df)}")
        print(f"   New rows created: {len(new_df) - len(df)}")
        
        return new_df
    
    def process_csv_file(self, input_file: str, output_file: str = None, 
                        address_column: str = None, address_columns: List[str] = None,
                        batch_size: int = 10, use_free_apis: bool = False, 
                        enable_batch_processing: bool = True, enable_split: bool = False,
                        use_gpt_split: bool = False) -> str:
        """
        Process a CSV or Excel file and standardize addresses using efficient batch processing
        
        Args:
            input_file: Path to input CSV or Excel file (.csv, .xlsx, .xls)
            output_file: Path to output CSV file (optional)
            address_column: Specific column name containing addresses (optional)
            address_columns: List of column names to combine into address (optional)
            batch_size: Number of addresses to process in each batch (default: 10)
            use_free_apis: Whether to use free APIs to fill missing components
            enable_batch_processing: Whether to use batch processing for efficiency
            enable_split: Whether to enable address splitting (default: False)
            use_gpt_split: Whether to use GPT for splitting instead of rules (default: False)
        
        Returns:
            Path to the output file
        """
        
        # Validate input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load CSV or Excel file based on file extension
        file_ext = os.path.splitext(input_file)[1].lower()
        try:
            if file_ext in ['.xlsx', '.xls']:
                # Read Excel file
                print(f"📊 Reading Excel file: {input_file}")
                df = pd.read_excel(input_file)
            elif file_ext in ['.csv', '.txt']:
                # Read CSV file with encoding detection
                print(f"📄 Reading CSV file: {input_file}")
                try:
                    df = pd.read_csv(input_file, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(input_file, encoding='latin-1')
            else:
                raise Exception(f"Unsupported file format: {file_ext}. Supported formats: .csv, .xlsx, .xls")
        except Exception as e:
            raise Exception(f"Could not read file: {str(e)}")
        
        print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        
        if use_free_apis:
            print(f"🌐 Free API enhancement: ENABLED")
            print(f"   Available APIs: {', '.join([k for k, v in self.free_apis.items() if v['enabled']])}")
        else:
            print(f"🌐 Free API enhancement: DISABLED")
        
        if enable_split:
            if self.address_splitter:
                # Update splitter mode if GPT splitting is requested
                if use_gpt_split and not self.address_splitter.use_gpt:
                    self.address_splitter.use_gpt = True
                    split_mode = "GPT-based"
                elif self.address_splitter.use_gpt:
                    split_mode = "GPT-based"
                else:
                    split_mode = "Rule-based"
                print(f"✂️  Address splitting: ENABLED ({split_mode})")
            else:
                print(f"⚠️  Address splitting requested but splitter not available - DISABLED")
                enable_split = False
        else:
            print(f"✂️  Address splitting: DISABLED")
        
        # Determine processing method based on parameters
        result_file = None
        
        if address_columns:
            # User-specified columns to combine
            result_file = self.process_user_specified_columns(df, address_columns, output_file, use_free_apis, enable_split)
        elif address_column:
            # Single specified column
            result_file = self.process_regular_address_format(df, address_column, output_file, use_free_apis, enable_batch_processing, enable_split)
        else:
            # Auto-detect format (existing logic)
            # Check if this is a site address structure
            is_site_format = self.detect_site_address_columns(df)
            
            if is_site_format:
                # Process site address format
                result_file = self.process_site_address_format(df, output_file, use_free_apis, enable_split)
            else:
                # Process regular address format
                result_file = self.process_regular_address_format(df, address_column, output_file, use_free_apis, enable_batch_processing, enable_split)
        
        # Archive input file if it was from inbound directory and processing was successful
        if result_file:
            self.archive_single_inbound_file(input_file)
            
        return result_file
    
    def process_site_address_format(self, df: pd.DataFrame, output_file: str = None, use_free_apis: bool = False, enable_split: bool = False) -> str:
        """Process CSV with site address column structure"""
        
        print(f"\n🏢 Processing Site Address Format")
        print("=" * 50)
        print("📋 Processing mode: ADD STANDARDIZED COLUMNS")
        print("   Original columns preserved + new standardized columns added")
        
        # Detect country column
        country_column = self.detect_country_column(df)
        
        # Add combined address column
        df['Combined_Address'] = df.apply(self.combine_site_address_fields, axis=1)
        
        # Handle address splitting if enabled
        if enable_split and self.address_splitter:
            print(f"\n✂️  Address splitting is ENABLED - analyzing addresses...")
            df = self.apply_address_splitting(df, ['Combined_Address'])
            print(f"✅ Address splitting completed. New row count: {len(df)}")
        
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
    
    def process_user_specified_columns(self, df: pd.DataFrame, address_columns: List[str], 
                                     output_file: str = None, use_free_apis: bool = False, enable_split: bool = False) -> str:
        """Process CSV with user-specified columns to combine into addresses - completely column name independent"""
        
        print(f"\n🎯 Processing User-Specified Address Columns")
        print("=" * 60)
        print("📋 Processing mode: USER-SPECIFIED COLUMNS")
        print(f"   Columns to combine: {', '.join(address_columns)}")
        print("   Original columns preserved + new standardized columns added")
        
        # Validate that all specified columns exist
        missing_columns = [col for col in address_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Error: Missing columns in CSV: {', '.join(missing_columns)}")
            print(f"   Available columns: {', '.join(df.columns.tolist())}")
            raise ValueError(f"Missing columns: {', '.join(missing_columns)}")
        
        # Add combined address column using user-specified columns
        df['Combined_Address'] = df.apply(lambda row: self.combine_address_columns(row, address_columns), axis=1)
        
        # Handle address splitting if enabled
        if enable_split and self.address_splitter:
            print(f"\n✂️  Address splitting is ENABLED - analyzing addresses...")
            df = self.apply_address_splitting(df, ['Combined_Address'])
            print(f"✅ Address splitting completed. New row count: {len(df)}")
        
        # Show sample of combined addresses
        print(f"\n📋 Sample combined addresses:")
        for i in range(min(3, len(df))):
            if df.iloc[i]['Combined_Address']:
                print(f"   Row {i+1}: {df.iloc[i]['Combined_Address'][:80]}...")
        
        # Add standardization result columns
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
        df[f"{base_col_name}_country_code"] = ""
        df[f"{base_col_name}_district"] = ""
        df[f"{base_col_name}_region"] = ""
        df[f"{base_col_name}_suburb"] = ""
        df[f"{base_col_name}_locality"] = ""
        df[f"{base_col_name}_sublocality"] = ""
        df[f"{base_col_name}_canton"] = ""
        df[f"{base_col_name}_prefecture"] = ""
        df[f"{base_col_name}_oblast"] = ""
        df[f"{base_col_name}_confidence"] = ""
        df[f"{base_col_name}_issues"] = ""
        df[f"{base_col_name}_status"] = ""
        df[f"{base_col_name}_api_source"] = ""
        df[f"{base_col_name}_latitude"] = ""
        df[f"{base_col_name}_longitude"] = ""
        df[f"{base_col_name}_address_id"] = ""
        df[f"{base_col_name}_from_cache"] = ""
        
        # Process each combined address
        total_rows = len(df)
        processed_count = 0
        success_count = 0
        error_count = 0
        cached_count = 0
        
        print(f"\n🚀 Processing {total_rows} combined addresses...")
        
        for df_index, row in df.iterrows():
            combined_address = row['Combined_Address']
            
            if not combined_address or pd.isna(combined_address):
                # Handle empty combined address
                df.at[df_index, f"{base_col_name}_status"] = "skipped"
                df.at[df_index, f"{base_col_name}_issues"] = "empty_combined_address"
                df.at[df_index, f"{base_col_name}_confidence"] = "n/a"
                error_count += 1
                processed_count += 1
                continue
            
            # Standardize the combined address
            result = self.standardize_single_address(combined_address, df_index)
            
            # Update DataFrame with results
            if result:
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
                df.at[df_index, f"{base_col_name}_country_code"] = result.get('country_code', '')
                df.at[df_index, f"{base_col_name}_district"] = result.get('district', '')
                df.at[df_index, f"{base_col_name}_region"] = result.get('region', '')
                df.at[df_index, f"{base_col_name}_suburb"] = result.get('suburb', '')
                df.at[df_index, f"{base_col_name}_locality"] = result.get('locality', '')
                df.at[df_index, f"{base_col_name}_sublocality"] = result.get('sublocality', '')
                df.at[df_index, f"{base_col_name}_canton"] = result.get('canton', '')
                df.at[df_index, f"{base_col_name}_prefecture"] = result.get('prefecture', '')
                df.at[df_index, f"{base_col_name}_oblast"] = result.get('oblast', '')
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
            if (processed_count + 1) % 5 == 0 or processed_count == total_rows - 1:
                print(f"Progress: {processed_count + 1}/{total_rows} ({(processed_count + 1)/total_rows*100:.1f}%) - {cached_count} cached")
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        # Print enhanced summary with cache statistics
        print(f"\n📊 Processing Summary:")
        print(f"   Total processed: {processed_count}")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Cached addresses: {cached_count}/{processed_count} ({cached_count/processed_count*100:.1f}%)" if processed_count > 0 else "   Cached addresses: 0/0 (0.0%)")
        print(f"   New addresses processed: {processed_count - cached_count}")
        
        return self.save_and_summarize_results(df, output_file, processed_count, success_count, error_count, ["Combined_Address"])

    def process_regular_address_format(self, df: pd.DataFrame, address_column: str = None, output_file: str = None, use_free_apis: bool = False, enable_batch_processing: bool = True, enable_split: bool = False) -> str:
        """Process CSV with regular address format"""
        
        # Detect country column
        country_column = self.detect_country_column(df)
        
        # Check if we have separated address components
        separated_components = self.detect_separated_address_components(df)
        
        if separated_components and len(separated_components) >= 2:
            # We have separated address components
            print(f"✅ Detected separated address components:")
            for component, column in separated_components.items():
                print(f"   {component}: '{column}'")
            
            # IMPORTANT: Split Address1 BEFORE combining with other components
            if enable_split and self.address_splitter and 'address_line_1' in separated_components:
                addr1_col = separated_components['address_line_1']
                addr2_col = separated_components.get('address_line_2')
                
                print(f"\n✂️  Address splitting is ENABLED - splitting Address1 field before combining...")
                # Apply splitting ONLY to Address1
                df = self.apply_address_splitting(df, [addr1_col])
                print(f"✅ Address splitting completed on '{addr1_col}'. New row count: {len(df)}")
            
            # NOW combine the (possibly split) components
            print(f"\n🔗 Combining address components into complete addresses...")
            df['Combined_Address'] = df.apply(lambda row: self.combine_separated_address_components(row, separated_components), axis=1)
            
            # Use the combined address column for processing
            address_columns = ['Combined_Address']
            print(f"✅ Combined address column created: 'Combined_Address'")
            
        else:
            # Detect address columns using existing logic
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
            
            # Handle address splitting if enabled (for non-separated formats)
            if enable_split and self.address_splitter:
                print(f"\n✂️  Address splitting is ENABLED - analyzing addresses...")
                df = self.apply_address_splitting(df, address_columns)
                print(f"✅ Address splitting completed. New row count: {len(df)}")
        
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
            df[f"{base_col_name}_country_code"] = ""
            df[f"{base_col_name}_district"] = ""
            df[f"{base_col_name}_region"] = ""
            df[f"{base_col_name}_suburb"] = ""
            df[f"{base_col_name}_locality"] = ""
            df[f"{base_col_name}_sublocality"] = ""
            df[f"{base_col_name}_canton"] = ""
            df[f"{base_col_name}_prefecture"] = ""
            df[f"{base_col_name}_oblast"] = ""
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
            
            if enable_batch_processing:
                # Use batch processing
                try:
                    from app.config.address_config import PROMPT_CONFIG
                    batch_size = PROMPT_CONFIG.get("batch_size", 5)
                except ImportError:
                    batch_size = 5
                    
                print(f"🚀 Processing {total_rows} addresses...")
                print(f"   Using batch processing (batch size: {batch_size})")
                
                # Process in batches
                for batch_start in range(0, total_rows, batch_size):
                    batch_end = min(batch_start + batch_size, total_rows)
                    
                    print(f"   Processing batch {batch_start//batch_size + 1}: rows {batch_start+1}-{batch_end}")
                    batch_extract_start = time.time()
                    
                    batch_df = df.iloc[batch_start:batch_end]
                    
                    # Extract addresses for this batch
                    batch_addresses = []
                    batch_countries = []
                    batch_indices = []
                    
                    for idx, (_, row) in enumerate(batch_df.iterrows()):
                        address = row[addr_col]
                        batch_addresses.append(address)
                        
                        # Get target country from column if available
                        target_country = None
                        if country_column and country_column in row:
                            target_country = str(row[country_column]).strip() if pd.notna(row[country_column]) else None
                        batch_countries.append(target_country)
                        batch_indices.append(batch_start + idx)
                    
                    batch_extract_time = time.time() - batch_extract_start
                    print(f"   ⏱️  Batch extraction time: {batch_extract_time:.2f}s")
                    
                    # Process this batch
                    batch_api_start = time.time()
                    if len(batch_addresses) > 1:
                        # Use the most common country in the batch, or None
                        common_country = max(set(batch_countries), key=batch_countries.count) if any(batch_countries) else None
                        
                        batch_results = self.standardize_addresses_batch(
                            batch_addresses, 
                            batch_start, 
                            target_country=common_country, 
                            use_free_apis=use_free_apis
                        )
                    else:
                        # Single address processing for small batches
                        batch_results = []
                        for i, address in enumerate(batch_addresses):
                            result = self.standardize_single_address(
                                address, 
                                batch_start + i, 
                                target_country=batch_countries[i],
                                use_free_apis=use_free_apis
                            )
                            batch_results.append(result)
                    
                    batch_api_time = time.time() - batch_api_start
                    print(f"   ⏱️  API processing time: {batch_api_time:.2f}s")
                    
                    # Update DataFrame with batch results
                    df_update_start = time.time()
                    
                    for i, result in enumerate(batch_results):
                        df_index = batch_start + i
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
                        df.at[df_index, f"{base_col_name}_country_code"] = result.get('country_code', '')
                        df.at[df_index, f"{base_col_name}_district"] = result.get('district', '')
                        df.at[df_index, f"{base_col_name}_region"] = result.get('region', '')
                        df.at[df_index, f"{base_col_name}_suburb"] = result.get('suburb', '')
                        df.at[df_index, f"{base_col_name}_locality"] = result.get('locality', '')
                        df.at[df_index, f"{base_col_name}_sublocality"] = result.get('sublocality', '')
                        df.at[df_index, f"{base_col_name}_canton"] = result.get('canton', '')
                        df.at[df_index, f"{base_col_name}_prefecture"] = result.get('prefecture', '')
                        df.at[df_index, f"{base_col_name}_oblast"] = result.get('oblast', '')
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
                    
                    df_update_time = time.time() - df_update_start
                    print(f"   ⏱️  DataFrame update time: {df_update_time:.2f}s ({len(batch_results)} addresses × 26 columns)")
                
                print(f"✅ Batch processing completed: {processed_count} addresses processed")
            else:
                # Use individual processing
                print(f"🔄 Processing {total_rows} addresses individually...")
                
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
                    df.at[index, f"{base_col_name}_country_code"] = result.get('country_code', '')
                    df.at[index, f"{base_col_name}_district"] = result.get('district', '')
                    df.at[index, f"{base_col_name}_region"] = result.get('region', '')
                    df.at[index, f"{base_col_name}_suburb"] = result.get('suburb', '')
                    df.at[index, f"{base_col_name}_locality"] = result.get('locality', '')
                    df.at[index, f"{base_col_name}_sublocality"] = result.get('sublocality', '')
                    df.at[index, f"{base_col_name}_canton"] = result.get('canton', '')
                    df.at[index, f"{base_col_name}_prefecture"] = result.get('prefecture', '')
                    df.at[index, f"{base_col_name}_oblast"] = result.get('oblast', '')
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
        
        print(f"\n⏱️  Starting save_and_summarize_results...")
        save_start = time.time()
        result = self.save_and_summarize_results(df, output_file, total_processed, total_success, total_errors, address_columns)
        save_time = time.time() - save_start
        print(f"⏱️  save_and_summarize_results took: {save_time:.2f}s")
        return result
    
    def save_and_summarize_results(self, df: pd.DataFrame, output_file: str, processed_count: int, success_count: int, error_count: int, address_columns: List[str]) -> str:
        """Save results and display summary"""
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"addresses_standardized_{timestamp}.csv"
            # Save to outbound directory by default
            output_file = str(self.outbound_dir / output_filename)
        
        # Ensure output file is in outbound directory if not specified otherwise
        output_path = Path(output_file)
        if not output_path.is_absolute() and output_path.parent == Path('.'):
            output_file = str(self.outbound_dir / output_path.name)
        
        # Save results with proper CSV escaping to handle commas in addresses
        # Always use UTF-8 with BOM to properly handle Unicode characters (accented letters, etc.)
        # UTF-8 BOM ensures Excel and other tools correctly interpret the encoding
        try:
            df.to_csv(output_file, index=False, encoding='utf-8-sig', quoting=1)  # utf-8-sig adds BOM
            print(f"✅ File saved with UTF-8 encoding (supports all Unicode characters)")
        except Exception as e:
            # Log the error but don't fallback to latin-1 as it corrupts Unicode characters
            print(f"⚠️ Error saving file with UTF-8: {e}")
            # Retry with standard UTF-8 without BOM as a fallback
            df.to_csv(output_file, index=False, encoding='utf-8', quoting=1)
            print(f"✅ File saved with UTF-8 encoding (no BOM)")
        
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

    def compare_addresses_with_openai(self, address1: str, address2: str, country: str = None) -> Dict[str, Any]:
        """
        Compare two addresses using OpenAI and return comprehensive match analysis
        
        Args:
            address1: First address to compare
            address2: Second address to compare
            country: Optional target country context
        
        Returns:
            Dictionary with comparison results and match score
        """
        print(f"\n🔍 Comparing addresses with OpenAI:")
        print(f"   Address 1: {address1}")
        print(f"   Address 2: {address2}")
        
        # First standardize both addresses (use existing functionality)
        print("🤖 Standardizing both addresses...")
        std_result1 = self.process_single_address_input(address1, country, 'json')
        std_result2 = self.process_single_address_input(address2, country, 'json')
        
        # Then ask OpenAI to compare them
        comparison_prompt = self._create_comparison_prompt(
            address1, address2, 
            std_result1.get('formatted_address', ''), 
            std_result2.get('formatted_address', ''),
            country
        )
        
        try:
            from app.services.azure_openai import compare_addresses
            
            # Use the new Azure OpenAI comparison service
            comparison_result = compare_addresses(comparison_prompt, target_country=country)
            
            if comparison_result and isinstance(comparison_result, dict):
                # Check if it's the full OpenAI response or just the content
                if 'choices' in comparison_result and comparison_result['choices']:
                    # Extract content from full response
                    content = comparison_result['choices'][0]['message']['content']
                    parsed_comparison = self._parse_comparison_result(content)
                elif 'overall_score' in comparison_result:
                    # The Azure service already parsed the JSON for us
                    parsed_comparison = comparison_result
                else:
                    # Assume it's already parsed content
                    parsed_comparison = self._parse_comparison_result(str(comparison_result))
                
                # Return flattened structure for easier CLI handling
                return {
                    'original_address_1': address1,
                    'original_address_2': address2,
                    'standardized_address_1': std_result1.get('formatted_address', ''),
                    'standardized_address_2': std_result2.get('formatted_address', ''),
                    'match_level': parsed_comparison.get('match_level', 'NO_MATCH'),
                    'confidence_score': parsed_comparison.get('overall_score', 0),
                    'analysis': parsed_comparison.get('explanation', 'No analysis available'),
                    'method_used': 'azure_openai',
                    'timestamp': datetime.now().isoformat(),
                    'likely_same_address': parsed_comparison.get('likely_same_address', False),
                    'confidence': parsed_comparison.get('confidence', 'low'),
                    'component_analysis': parsed_comparison.get('component_analysis', {}),
                    'key_differences': parsed_comparison.get('key_differences', []),
                    'key_similarities': parsed_comparison.get('key_similarities', [])
                }
            else:
                return self._fallback_comparison(address1, address2, std_result1, std_result2)
                
        except Exception as e:
            print(f"❌ OpenAI comparison failed: {e}")
            return self._fallback_comparison(address1, address2, std_result1, std_result2)

    def _create_comparison_prompt(self, addr1: str, addr2: str, std_addr1: str, std_addr2: str, country: str = None) -> str:
        """Create a comprehensive prompt for address comparison using config"""
        
        try:
            from app.config.address_config import ADDRESS_COMPARISON_PROMPT
            
            country_context = f"\nContext: Both addresses are expected to be in {country}." if country else ""
            
            # Format the prompt template with actual addresses
            prompt = ADDRESS_COMPARISON_PROMPT.format(
                addr1=addr1,
                std_addr1=std_addr1,
                addr2=addr2,
                std_addr2=std_addr2,
                country_context=country_context
            )
            
            return prompt
            
        except ImportError:
            # Fallback to basic prompt if config not available
            country_context = f"\nContext: Both addresses are expected to be in {country}." if country else ""
            
            fallback_prompt = f"""Compare these two addresses and provide a match score (0-100) and analysis.

Address 1: "{addr1}" (Standardized: "{std_addr1}")
Address 2: "{addr2}" (Standardized: "{std_addr2}"){country_context}

Return JSON with: overall_score, match_level, likely_same_address, confidence, explanation"""
            
            return fallback_prompt

    def _parse_comparison_result(self, ai_response: str) -> Dict[str, Any]:
        """Parse and validate OpenAI comparison response"""
        try:
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                comparison_data = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ['overall_score', 'match_level', 'likely_same_address', 'confidence']
                for field in required_fields:
                    if field not in comparison_data:
                        comparison_data[field] = self._get_default_value(field)
                
                # Ensure score is within valid range
                score = comparison_data.get('overall_score', 0)
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    comparison_data['overall_score'] = 0
                
                # Validate match level
                valid_levels = ['EXACT', 'HIGH', 'MEDIUM', 'LOW', 'NO_MATCH']
                if comparison_data.get('match_level') not in valid_levels:
                    comparison_data['match_level'] = self._score_to_match_level(comparison_data['overall_score'])
                
                return comparison_data
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"⚠️ Could not parse OpenAI comparison result: {e}")
            return self._create_fallback_comparison_result()

    def _score_to_match_level(self, score: float) -> str:
        """Convert numeric score to match level"""
        if score >= 95: return "EXACT"
        elif score >= 85: return "HIGH" 
        elif score >= 70: return "MEDIUM"
        elif score >= 30: return "LOW"
        else: return "NO_MATCH"

    def _get_default_value(self, field: str):
        """Get default values for missing fields"""
        defaults = {
            'overall_score': 0,
            'match_level': 'NO_MATCH',
            'likely_same_address': False,
            'confidence': 'low'
        }
        return defaults.get(field, '')

    def _create_fallback_comparison_result(self) -> Dict[str, Any]:
        """Create a fallback comparison result when OpenAI fails"""
        return {
            'overall_score': 0,
            'match_level': 'NO_MATCH',
            'likely_same_address': False,
            'confidence': 'low',
            'explanation': 'Comparison could not be completed using OpenAI',
            'error': 'Failed to analyze addresses'
        }

    def _fallback_comparison(self, address1: str, address2: str, std_result1: Dict[str, Any], std_result2: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback comparison using simple string matching when OpenAI fails"""
        print("⚠️ Using fallback comparison method...")
        
        # Simple string similarity as fallback
        formatted1 = std_result1.get('formatted_address', address1).lower().strip()
        formatted2 = std_result2.get('formatted_address', address2).lower().strip()
        
        # Basic similarity calculation
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, formatted1, formatted2).ratio()
        score = int(similarity * 100)
        
        return {
            'original_address_1': address1,
            'original_address_2': address2,
            'standardized_address_1': std_result1.get('formatted_address', ''),
            'standardized_address_2': std_result2.get('formatted_address', ''),
            'match_level': self._score_to_match_level(score),
            'confidence_score': score,
            'analysis': f'Fallback comparison using string similarity: {score}%',
            'method_used': 'string_similarity_fallback',
            'timestamp': datetime.now().isoformat(),
            'likely_same_address': score >= 80,
            'confidence': 'low',
            'component_analysis': {},
            'key_differences': [],
            'key_similarities': []
        }
    
    def process_csv_comparison_file(self, input_file, output_file=None, batch_size=5):
        """
        Process a CSV file containing pairs of addresses for comparison.
        
        Expected CSV format:
        - address1, address2 (two columns with addresses to compare)
        OR
        - id, address1, address2 (with an ID column)
        
        Args:
            input_file (str): Path to input CSV file (can be filename only if in inbound directory)
            output_file (str): Path to output CSV file (auto-generated in outbound if not provided)
            batch_size (int): Number of comparisons to process at once
            
        Returns:
            str: Path to the generated output file
        """
        try:
            # Handle file path - check if it's just a filename (look in inbound) or full path
            input_path = Path(input_file)
            if not input_path.is_absolute() and not input_path.exists():
                # Try to find it in inbound directory
                inbound_path = self.inbound_dir / input_file
                if inbound_path.exists():
                    input_path = inbound_path
                    print(f"📥 Found input file in inbound directory: {input_file}")
                else:
                    # If not found, use original path (might be relative to current dir)
                    input_path = Path(input_file)
            
            # Verify input file exists
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            # Read the input file; support both CSV and Excel (xlsx/xls)
            ext = input_path.suffix.lower()
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(str(input_path))
            else:
                # Read the CSV file with automatic encoding detection and robust parsing
                try:
                    df = read_csv_with_encoding_detection(str(input_path))
                except Exception:
                    # Fallback to a robust read that skips bad lines
                    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                        df = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip', dtype=str)
            
            # Detect column structure
            columns = df.columns.tolist()
            if len(columns) < 2:
                raise ValueError("CSV file must have at least 2 columns for address comparison")
            
            # Determine column mapping
            if len(columns) == 2:
                # Assume format: address1, address2
                addr1_col, addr2_col = columns[0], columns[1]
                id_col = None
            elif len(columns) >= 3:
                # Assume format: id, address1, address2
                id_col, addr1_col, addr2_col = columns[0], columns[1], columns[2]
            
            print(f"📊 Detected columns:")
            if id_col:
                print(f"   ID column: {id_col}")
            print(f"   Address 1 column: {addr1_col}")
            print(f"   Address 2 column: {addr2_col}")
            print(f"   Total rows to compare: {len(df):,}")
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = input_path.stem
                output_file = self.outbound_dir / f"{base_name}_comparison_results_{timestamp}.csv"
            else:
                # If output file provided, handle path
                output_path = Path(output_file)
                if not output_path.is_absolute():
                    # If relative path, put it in outbound directory
                    output_file = self.outbound_dir / output_file
                else:
                    output_file = output_path
            
            print(f"📤 Output will be saved to: {output_file}")
            
            # Prepare results list
            results = []
            
            # Process in batches
            total_rows = len(df)
            processed = 0
            
            print(f"\n🚀 Starting efficient batch address comparison processing...")
            print(f"   📊 Using batch size: {batch_size} (multiple pairs per API call)")
            start_time = time.time()
            
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                batch_df = df.iloc[batch_start:batch_end]
                
                print(f"📦 Processing batch {batch_start//batch_size + 1}: rows {batch_start + 1}-{batch_end}")
                
                # Prepare address pairs for efficient batch processing
                address_pairs = []
                row_metadata = []
                
                for idx, row in batch_df.iterrows():
                    address1 = str(row[addr1_col]).strip() if pd.notna(row[addr1_col]) else ""
                    address2 = str(row[addr2_col]).strip() if pd.notna(row[addr2_col]) else ""
                    
                    address_pairs.append({
                        'address1': address1,
                        'address2': address2
                    })
                    
                    # Store row metadata for later
                    row_data = {'original_row_index': idx}
                    if id_col:
                        row_data['id'] = row[id_col] if pd.notna(row[id_col]) else ''
                    row_metadata.append(row_data)
                
                try:
                    # Use efficient batch comparison with optimal batch size from config
                    batch_results = compare_multiple_addresses(address_pairs, batch_size=batch_size)
                    
                    # Process batch results
                    for i, comparison_result in enumerate(batch_results):
                        try:
                            metadata = row_metadata[i] if i < len(row_metadata) else {}
                            pair = address_pairs[i] if i < len(address_pairs) else {'address1': '', 'address2': ''}
                            
                            # Handle empty addresses
                            if not pair.get('address1', '').strip() or not pair.get('address2', '').strip():
                                result_row = {
                                    'original_address_1': pair.get('address1', ''),
                                    'original_address_2': pair.get('address2', ''),
                                    'standardized_address_1': '',
                                    'standardized_address_2': '',
                                    'match_level': 'NO_MATCH',
                                    'confidence_score': 0,
                                    'analysis': 'One or both addresses are empty',
                                    'method_used': 'validation_check',
                                    'timestamp': datetime.now().isoformat(),
                                    'status': 'empty_address'
                                }
                            else:
                                result_row = {
                                    'original_address_1': comparison_result.get('original_address_1', pair.get('address1', '')),
                                    'original_address_2': comparison_result.get('original_address_2', pair.get('address2', '')),
                                    'standardized_address_1': comparison_result.get('standardized_address_1', ''),
                                    'standardized_address_2': comparison_result.get('standardized_address_2', ''),
                                    'match_level': comparison_result.get('match_level', 'UNKNOWN'),
                                    'confidence_score': comparison_result.get('confidence_score', comparison_result.get('overall_score', 0)),
                                    'analysis': comparison_result.get('analysis', 'Batch comparison completed'),
                                    'method_used': comparison_result.get('method_used', 'azure_openai_batch'),
                                    'timestamp': comparison_result.get('timestamp', datetime.now().isoformat()),
                                    'status': 'success' if 'error' not in comparison_result else 'error'
                                }
                            
                            # Add ID if present
                            if 'id' in metadata:
                                result_row['id'] = metadata['id']
                            
                            results.append(result_row)
                            processed += 1
                            
                        except Exception as result_error:
                            # Handle individual result processing errors
                            metadata = row_metadata[i] if i < len(row_metadata) else {}
                            pair = address_pairs[i] if i < len(address_pairs) else {'address1': '', 'address2': ''}
                            
                            error_result = {
                                'original_address_1': pair.get('address1', ''),
                                'original_address_2': pair.get('address2', ''),
                                'standardized_address_1': '',
                                'standardized_address_2': '',
                                'match_level': 'ERROR',
                                'confidence_score': 0,
                                'analysis': f'Error processing result: {str(result_error)}',
                                'method_used': 'error_handling',
                                'timestamp': datetime.now().isoformat(),
                                'status': 'error'
                            }
                            
                            if 'id' in metadata:
                                error_result['id'] = metadata['id']
                            
                            results.append(error_result)
                            processed += 1
                            
                except Exception as batch_error:
                    print(f"   ❌ Batch processing failed, falling back to individual processing: {str(batch_error)}")
                    
                    # Fallback to individual processing for this batch
                    for i, (pair, metadata) in enumerate(zip(address_pairs, row_metadata)):
                        try:
                            address1 = pair['address1']
                            address2 = pair['address2']
                            
                            if not address1 or not address2:
                                # Handle empty addresses
                                result_row = {
                                    'original_address_1': address1,
                                    'original_address_2': address2,
                                    'standardized_address_1': '',
                                    'standardized_address_2': '',
                                    'match_level': 'NO_MATCH',
                                    'confidence_score': 0,
                                    'analysis': 'One or both addresses are empty',
                                    'method_used': 'validation_check',
                                    'timestamp': datetime.now().isoformat(),
                                    'status': 'empty_address'
                                }
                            else:
                                # Perform individual comparison as fallback
                                comparison_result = self.compare_addresses_with_openai(address1, address2)
                                
                                result_row = {
                                    'original_address_1': address1,
                                    'original_address_2': address2,
                                    'standardized_address_1': comparison_result['standardized_address_1'],
                                    'standardized_address_2': comparison_result['standardized_address_2'],
                                    'match_level': comparison_result['match_level'],
                                    'confidence_score': comparison_result['confidence_score'],
                                    'analysis': comparison_result['analysis'],
                                    'method_used': comparison_result['method_used'],
                                    'timestamp': comparison_result['timestamp'],
                                    'status': 'success'
                                }
                            
                            # Add ID if present
                            if 'id' in metadata:
                                result_row['id'] = metadata['id']
                            
                            results.append(result_row)
                            processed += 1
                            
                        except Exception as individual_error:
                            print(f"   ⚠️  Error processing individual comparison: {str(individual_error)}")
                            
                            # Create error result for individual failure
                            error_result = {
                                'original_address_1': pair.get('address1', ''),
                                'original_address_2': pair.get('address2', ''),
                                'standardized_address_1': '',
                                'standardized_address_2': '',
                                'match_level': 'ERROR',
                                'confidence_score': 0,
                                'analysis': f'Individual processing error: {str(individual_error)}',
                                'method_used': 'error_fallback',
                                'timestamp': datetime.now().isoformat(),
                                'status': 'error'
                            }
                            
                            if 'id' in metadata:
                                error_result['id'] = metadata['id']
                            
                            results.append(error_result)
                            processed += 1
                
                # Progress indicator
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"   ✓ Processed {processed}/{total_rows} ({processed/total_rows*100:.1f}%) - {rate:.1f} comparisons/sec")
                
                # Brief pause between batches
                time.sleep(0.1)
            
            # Create results DataFrame
            results_df = pd.DataFrame(results)
            
            # Reorder columns to put ID first if present
            if id_col:
                column_order = ['id'] + [col for col in results_df.columns if col != 'id']
                results_df = results_df[column_order]
            
            # Save results with UTF-8-BOM encoding to properly handle Unicode characters
            # UTF-8-BOM ensures Excel and other tools correctly interpret special characters
            results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"✅ Comparison results saved with UTF-8 encoding (supports all Unicode characters)")
            
            # Calculate summary statistics
            elapsed_time = time.time() - start_time
            avg_rate = processed / elapsed_time if elapsed_time > 0 else 0
            
            match_counts = results_df['match_level'].value_counts()
            
            print(f"\n✅ Address comparison processing completed!")
            print(f"📊 Processing Summary:")
            print(f"   Total comparisons: {processed:,}")
            print(f"   Processing time: {elapsed_time:.1f} seconds")
            print(f"   Average rate: {avg_rate:.1f} comparisons/second")
            print(f"\n📈 Match Level Distribution:")
            for level, count in match_counts.items():
                percentage = (count / processed * 100) if processed > 0 else 0
                print(f"   {level}: {count:,} ({percentage:.1f}%)")
            
            # Archive input file if it was from inbound directory
            self.archive_single_inbound_file(input_file)
            
            return str(output_file)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_file}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Input file is empty: {input_file}")
        except Exception as e:
            raise Exception(f"Error processing CSV comparison file: {e}")

def main():
    """Enhanced command line interface supporting both CSV files and direct address input"""
    parser = argparse.ArgumentParser(
        description='AddressIQ: Standardize addresses from CSV files or direct input',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process CSV file
  python csv_address_processor.py addresses.csv

  # Process all files in inbound directory
  python csv_address_processor.py --batch-process

  # Process with user-specified columns (column name independent!)
  python csv_address_processor.py addresses.csv --address-columns "street,city,state,zip"
  python csv_address_processor.py data.csv --address-columns "Site_Address_Line1,Site_City,Site_State,Site_PostCode"

  # Process all comparison files in inbound directory
  python csv_address_processor.py --batch-compare

  # Process single address
  python csv_address_processor.py --address "123 Main St, NYC, NY"

  # Process multiple addresses
  python csv_address_processor.py --address "123 Main St, NYC" "456 Oak Ave, LA"

  # Compare two addresses
  python csv_address_processor.py --compare "123 Main St, NYC" "123 Main Street, New York"
  
  # Process CSV file for address comparison
  python csv_address_processor.py comparison_data.csv --compare-csv
  
  # With country specification
  python csv_address_processor.py --address "123 High St, London" --country "UK"
  
  # Different output formats
  python csv_address_processor.py --address "123 Main St" --format formatted
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        'input_file', 
        nargs='?', 
        help='CSV file containing addresses to process'
    )
    input_group.add_argument(
        '--address', '-a',
        nargs='+',
        help='Address(es) to process - single or multiple addresses'
    )
    input_group.add_argument(
        '--batch-process',
        action='store_true',
        help='Process all files in inbound directory'
    )
    input_group.add_argument(
        '--batch-compare',
        action='store_true',
        help='Process all comparison files in inbound directory'
    )
    input_group.add_argument(
        '--database',
        action='store_true',
        help='Process addresses from database (use with --db-* options)'
    )
    
    # Directory management options
    parser.add_argument(
        '--base-dir',
        help='Base directory for inbound/outbound/archive folders (default: current directory)'
    )
    
    # Options for CSV processing
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-c', '--column', help='Specific address column name (for CSV)')
    parser.add_argument('--address-columns', help='Comma-separated list of columns to combine into address (e.g., "address_line1,city,state,zip")')
    parser.add_argument('-b', '--batch-size', type=int, default=5, help='Batch size for processing (default: 5)')
    parser.add_argument('--no-free-apis', action='store_true', help='Disable free API enhancement')
    parser.add_argument('--enable-split', action='store_true', help='Enable address splitting based on rules (creates additional rows for split addresses)')
    parser.add_argument('--use-gpt-split', action='store_true', help='Use GPT-based splitting instead of rule-based (requires --enable-split)')
    
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
    
    # Address comparison options
    comparison_group = parser.add_argument_group('Address Comparison')
    comparison_group.add_argument(
        '--compare',
        nargs=2,
        metavar=('ADDRESS1', 'ADDRESS2'),
        help='Compare two addresses using OpenAI analysis'
    )
    comparison_group.add_argument(
        '--compare-csv',
        action='store_true',
        help='Enable address comparison mode for CSV files'
    )
    
    # Database processing options
    database_group = parser.add_argument_group('Database Processing')
    database_group.add_argument(
        '--db-type',
        choices=['sqlserver', 'azure_sql', 'mysql', 'postgresql', 'oracle', 'sqlite'],
        help='Database type (use with --database option)'
    )
    
    # Connection string option (alternative to individual parameters)
    database_group.add_argument('--db-connection-string', help='Database connection string (alternative to individual parameters)')
    
    # Individual connection parameters
    database_group.add_argument('--db-server', help='Database server (SQL Server/Azure SQL)')
    database_group.add_argument('--db-host', help='Database host (MySQL/PostgreSQL/Oracle)')
    database_group.add_argument('--db-port', type=int, help='Database port')
    database_group.add_argument('--db-name', help='Database name')
    database_group.add_argument('--db-username', help='Database username')
    database_group.add_argument('--db-password', help='Database password')
    database_group.add_argument('--db-path', help='Database file path (SQLite only)')
    
    # Query options
    database_group.add_argument('--db-query', help='Custom SQL query')
    database_group.add_argument('--db-table', help='Table name (if no custom query)')
    database_group.add_argument('--db-address-columns', help='Comma-separated address columns (recommended)')
    database_group.add_argument('--db-limit', type=int, default=5, help='Limit records to process (default: 5 for safety)')
    database_group.add_argument('--db-preview', action='store_true', help='Preview table structure and sample data')
    database_group.add_argument('--list-db-types', action='store_true', help='List supported database types')
    
    # Utility options
    parser.add_argument('--test-apis', action='store_true', help='Test free APIs and exit')
    parser.add_argument('--db-stats', action='store_true', help='Show database statistics and exit')
    
    args = parser.parse_args()
    
    # Create processor instance with base directory if specified
    processor = CSVAddressProcessor(base_directory=args.base_dir)
    
    # List supported database types if requested
    if args.list_db_types:
        supported = processor.get_supported_databases()
        print("📋 Supported Database Types:")
        print("=" * 30)
        if supported:
            for db_type in supported:
                print(f"  ✅ {db_type}")
        else:
            print("  ❌ No database drivers available")
        return
    
    # Database stats removed (no caching)
    if args.db_stats:
        print("📊 Database caching has been removed from AddressIQ")
        print("=" * 50)
        print("All addresses are now processed directly via API")
        print("No database dependency required")
        return
    
    # Test APIs if requested
    if args.test_apis:
        processor.test_free_apis()
        return
    
    # Handle address comparison
    if args.compare:
        address1, address2 = args.compare
        print(f"🔍 Comparing addresses:")
        print(f"   Address 1: {address1}")
        print(f"   Address 2: {address2}")
        print("-" * 80)
        
        try:
            result = processor.compare_addresses_with_openai(address1, address2)
            
            # Format output based on format argument
            if args.format == 'json':
                print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
            elif args.format == 'formatted':
                print(f"📊 Comparison Results:")
                print(f"   Match Level: {result['match_level']}")
                print(f"   Confidence Score: {result['confidence_score']}")
                print(f"   Analysis: {result['analysis']}")
                print(f"   Method Used: {result['method_used']}")
                print(f"\n📍 Standardized Addresses:")
                print(f"   Address 1: {result['standardized_address_1']}")
                print(f"   Address 2: {result['standardized_address_2']}")
            elif args.format == 'detailed':
                print(f"📊 Detailed Comparison Results:")
                print(f"   Match Level: {result['match_level']}")
                print(f"   Confidence Score: {result['confidence_score']}")
                print(f"   Analysis: {result['analysis']}")
                print(f"   Method Used: {result['method_used']}")
                print(f"   Timestamp: {result['timestamp']}")
                print(f"\n📍 Standardized Addresses:")
                print(f"   Address 1: {result['standardized_address_1']}")
                print(f"   Address 2: {result['standardized_address_2']}")
            
            # Save to file if output specified
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str, ensure_ascii=False)
                print(f"\n📄 Comparison result saved to: {args.output}")
                
        except Exception as e:
            print(f"❌ Error comparing addresses: {e}")
            sys.exit(1)
        return
    
    # Handle database processing
    if args.database:
        if not args.db_type:
            print("❌ --db-type is required when using --database option")
            print("   Use --list-db-types to see supported database types")
            sys.exit(1)
        
        # Build connection parameters
        connection_params = {}
        
        # Check if connection string is provided
        if args.db_connection_string:
            connection_params['connection_string'] = args.db_connection_string
            print(f"🔗 Using connection string for {args.db_type}")
        else:
            # Build from individual parameters
            if args.db_type in ['sqlserver', 'azure_sql']:
                if not args.db_server:
                    print(f"❌ --db-server is required for {args.db_type} (or use --db-connection-string)")
                    sys.exit(1)
                connection_params['server'] = args.db_server
                connection_params['database'] = args.db_name or 'master'
                if args.db_username:
                    connection_params['username'] = args.db_username
                if args.db_password:
                    connection_params['password'] = args.db_password
                    
            elif args.db_type in ['mysql', 'postgresql', 'oracle']:
                if not args.db_host:
                    print(f"❌ --db-host is required for {args.db_type} (or use --db-connection-string)")
                    sys.exit(1)
                connection_params['host'] = args.db_host
                if args.db_port:
                    connection_params['port'] = args.db_port
                connection_params['database'] = args.db_name
                if args.db_username:
                    connection_params['username'] = args.db_username
                if args.db_password:
                    connection_params['password'] = args.db_password
                    
            elif args.db_type == 'sqlite':
                if not args.db_path:
                    print("❌ --db-path is required for SQLite (or use --db-connection-string)")
                    sys.exit(1)
                connection_params['database_path'] = args.db_path
        
        # Handle preview mode
        if args.db_preview:
            print("🔍 Previewing database table structure...")
            preview_result = processor.preview_database_table(
                args.db_type, 
                connection_params, 
                args.db_table
            )
            
            if preview_result['success']:
                if args.db_table:
                    print(f"\n📋 Table: {preview_result['table_name']}")
                    print(f"📊 Estimated rows: {preview_result.get('row_count_estimate', 'Unknown')}")
                    
                    print(f"\n📝 Columns ({len(preview_result['columns'])}):")
                    for col in preview_result['columns']:
                        print(f"   • {col['name']} ({col.get('type', 'unknown')})")
                    
                    if preview_result['detected_address_columns']:
                        print(f"\n🎯 Detected address columns:")
                        for col in preview_result['detected_address_columns']:
                            print(f"   • {col}")
                        print(f"\n💡 Suggestion: Use --db-address-columns '{','.join(preview_result['detected_address_columns'])}'")
                    
                    if preview_result['sample_data']:
                        print(f"\n📄 Sample data (first {len(preview_result['sample_data'])} rows):")
                        for i, row in enumerate(preview_result['sample_data'], 1):
                            print(f"   Row {i}:")
                            for key, value in list(row.items())[:3]:  # Show first 3 columns
                                print(f"     {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                            if len(row) > 3:
                                print(f"     ... and {len(row) - 3} more columns")
                            print()
                else:
                    print("\n📋 Available tables:")
                    for table in preview_result.get('available_tables', []):
                        print(f"   • {table}")
                    print("\n💡 Use --db-table <table_name> --db-preview to see table structure")
            else:
                print(f"❌ Preview failed: {preview_result['error']}")
            return
        
        # Parse address columns
        address_columns = None
        if args.db_address_columns:
            address_columns = [col.strip() for col in args.db_address_columns.split(',')]
        
        # Validate that either query or table is provided
        if not args.db_query and not args.db_table:
            print("❌ Either --db-query or --db-table must be specified")
            print("   Examples:")
            print("     --db-table 'customers'")
            print("     --db-query 'SELECT address, city FROM customers WHERE state=\"CA\"'")
            sys.exit(1)
        
        # Safety check: ensure reasonable limit
        limit = args.db_limit
        if limit is None:
            limit = 5  # Default safety limit
            print(f"⚠️  No limit specified, using default safety limit of {limit} records")
        elif limit > 10000:
            print(f"⚠️  Large limit specified ({limit} records)")
            response = input("   Continue? (y/N): ").strip().lower()
            if response != 'y':
                print("   Operation cancelled")
                sys.exit(0)
        
        # Warn if no address columns specified
        if not address_columns and not args.db_query:
            print("⚠️  No address columns specified. AddressIQ will auto-detect address columns.")
            print("   For better results, specify columns with --db-address-columns")
            print("   Example: --db-address-columns 'full_address,city,state'")
        
        print("🗃️ Starting database address processing...")
        print(f"   📊 Processing limit: {limit} records")
        if address_columns:
            print(f"   📍 Target columns: {', '.join(address_columns)}")
        print()
        try:
            result = processor.process_database_input(
                db_type=args.db_type,
                connection_params=connection_params,
                query=args.db_query,
                table_name=args.db_table,
                address_columns=address_columns,
                limit=limit,  # Use validated limit
                batch_size=args.batch_size,
                use_free_apis=not args.no_free_apis
            )
            
            if result['success']:
                print("\n🎉 Database processing completed successfully!")
                print(f"📊 Summary: {result['records_processed']} records processed")
                print(f"📁 Output file: {result['output_csv_path']}")
            else:
                print(f"\n❌ Database processing failed: {result['error']}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error in database processing: {e}")
            sys.exit(1)
        return
    
    # Process based on input type
    if args.batch_process:
        # Batch process all files in inbound directory
        print("🚀 Starting batch processing mode...")
        try:
            processor.process_all_inbound_files(
                batch_size=args.batch_size,
                use_free_apis=not args.no_free_apis,
                enable_split=args.enable_split,
                use_gpt_split=args.use_gpt_split
            )
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
            sys.exit(1)
            
    elif args.batch_compare:
        # Batch process all comparison files in inbound directory
        print("🚀 Starting batch comparison processing mode...")
        try:
            processor.process_all_inbound_comparison_files(
                batch_size=args.batch_size
            )
        except Exception as e:
            print(f"❌ Error in batch comparison processing: {e}")
            sys.exit(1)
            
    elif args.input_file:
        # CSV file processing
        print(f"📁 Processing CSV file: {args.input_file}")
        try:
            # Check if comparison mode is enabled for CSV
            if args.compare_csv:
                output_file = processor.process_csv_comparison_file(
                    input_file=args.input_file,
                    output_file=args.output,
                    batch_size=args.batch_size
                )
                print(f"\n✅ Address comparison processing completed successfully!")
                print(f"📁 Comparison results saved to: {output_file}")
            else:
                output_file = processor.process_csv_file(
                    input_file=args.input_file,
                    output_file=args.output,
                    address_column=args.column,
                    address_columns=args.address_columns.split(',') if args.address_columns else None,
                    batch_size=args.batch_size,
                    use_free_apis=not args.no_free_apis,
                    enable_split=args.enable_split,
                    use_gpt_split=args.use_gpt_split
                )
                print(f"\n✅ Processing completed successfully!")
                print(f"📁 Output saved to: {output_file}")
                
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            sys.exit(1)
            
    elif args.address:
        # Single or multiple address processing (auto-detected by number of arguments)
        if len(args.address) == 1:
            # Single address processing
            print(f"🏠 Processing single address")
            
            # Check if splitting is enabled
            if args.enable_split and processor.address_splitter:
                print(f"✂️  Address splitting: ENABLED ({'GPT-based' if args.use_gpt_split else 'Rule-based'})")
                
                # Parse the address to separate street address from geographic components
                # Use the same logic as CSV processing: split on commas, detect City/State/Zip pattern
                address_input = args.address[0]
                
                # Try to detect if address has geographic components separated by commas
                # Pattern: "Street Address, City, State Zip" or "Street Address, City, State, Zip"
                parts = [p.strip() for p in address_input.split(',')]
                
                street_address = None
                city = None
                state = None
                postal_code = None
                
                if len(parts) >= 3:
                    # Likely format: "Street, City, State/Zip" or "Street, City, State, Zip"
                    street_address = parts[0]
                    city = parts[1]
                    
                    # Check if last part contains state and/or zip
                    if len(parts) == 3:
                        # Format: "Street, City, State Zip"
                        state_zip = parts[2].strip()
                        # Try to extract state and zip
                        state_zip_match = re.match(r'^([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$', state_zip)
                        if state_zip_match:
                            state = state_zip_match.group(1)
                            postal_code = state_zip_match.group(2)
                        else:
                            state = state_zip
                    elif len(parts) == 4:
                        # Format: "Street, City, State, Zip"
                        state = parts[2]
                        postal_code = parts[3]
                    
                    print(f"   📍 Detected separated components:")
                    print(f"      Street: {street_address}")
                    print(f"      City: {city}")
                    print(f"      State: {state}")
                    print(f"      Zip: {postal_code}")
                    
                    # Split ONLY the street address portion
                    split_result = processor.address_splitter.analyze_and_split(street_address)
                    split_addresses = split_result['addresses']
                    reason = split_result['split_reason']
                    
                    # Reconstruct complete addresses by combining split street with city/state/zip
                    if len(split_addresses) > 1:
                        # Reconstruct complete addresses
                        complete_addresses = []
                        for split_street in split_addresses:
                            complete_addr_parts = [split_street, city]
                            if state and postal_code:
                                complete_addr_parts.append(f"{state} {postal_code}")
                            elif state:
                                complete_addr_parts.append(state)
                            elif postal_code:
                                complete_addr_parts.append(postal_code)
                            complete_addresses.append(", ".join(complete_addr_parts))
                        split_addresses = complete_addresses
                else:
                    # No geographic components detected, split the entire address
                    split_result = processor.address_splitter.analyze_and_split(address_input)
                    split_addresses = split_result['addresses']
                    reason = split_result['split_reason']
                
                if len(split_addresses) > 1:
                    print(f"✂️  Address split into {len(split_addresses)} addresses")
                    print(f"   Reason: {reason}")
                    
                    # Process each split address
                    results = []
                    for idx, split_addr in enumerate(split_addresses, 1):
                        print(f"\n   Processing split address {idx}/{len(split_addresses)}: {split_addr}")
                        result = processor.process_single_address_input(
                            split_addr, 
                            args.country, 
                            args.format
                        )
                        result['split_indicator'] = 'Yes'
                        result['split_address_number'] = f"{idx} of {len(split_addresses)}"
                        result['split_reason'] = reason
                        results.append(result)
                    
                    if args.output:
                        # Save to JSON file
                        with open(args.output, 'w', encoding='utf-8') as f:
                            json.dump(results, f, indent=2, ensure_ascii=False)
                        print(f"\n📄 Results saved to: {args.output}")
                    else:
                        # Print to console
                        print(f"\n📋 Results ({len(results)} addresses):")
                        for i, res in enumerate(results, 1):
                            print(f"\n--- Address {i} of {len(results)} ---")
                            if args.format == 'formatted':
                                print(f"   Original: {res.get('original_address', 'N/A')}")
                                print(f"   Formatted: {res.get('formatted_address', 'N/A')}")
                                print(f"   Confidence: {res.get('confidence', 'N/A')}")
                                print(f"   Split: {res.get('split_address_number', 'N/A')}")
                            else:
                                print(json.dumps(res, indent=2, ensure_ascii=False))
                else:
                    print(f"✂️  No split needed - processing as single address")
                    result = processor.process_single_address_input(
                        args.address[0], 
                        args.country, 
                        args.format
                    )
                    
                    if args.output:
                        with open(args.output, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        print(f"\n📄 Result saved to: {args.output}")
                    else:
                        print(f"\n📋 Result:")
                        if args.format == 'formatted':
                            print(f"   Original: {result.get('original_address', 'N/A')}")
                            print(f"   Formatted: {result.get('formatted_address', 'N/A')}")
                            print(f"   Confidence: {result.get('confidence', 'N/A')}")
                            print(f"   From cache: {result.get('from_cache', False)}")
                            print(f"   Status: {result.get('status', 'N/A')}")
                        else:
                            print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                # No splitting - process as is
                result = processor.process_single_address_input(
                    args.address[0], 
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
        else:
            # Multiple addresses processing
            print(f"🏠 Processing {len(args.address)} addresses")
            results = processor.process_multiple_addresses_input(
                args.address,
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
        # No input provided and no comparison requested, check if we need help
        if not (args.compare or args.test_apis or args.db_stats):
            parser.print_help()
            sys.exit(1)

if __name__ == "__main__":
    main()
