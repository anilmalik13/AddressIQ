#!/usr/bin/env python3
"""
Interactive Address Processor - Easy-to-use interface for address standardization
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_address_processor import CSVAddressProcessor

def interactive_mode():
    """Interactive mode for processing addresses"""
    processor = CSVAddressProcessor()
    
    print("🏠 AddressIQ Interactive Address Processor")
    print("=" * 50)
    print("Enter addresses to standardize. Type 'quit' to exit.")
    print("Commands:")
    print("  help     - Show this help")
    print("  stats    - Show database statistics")
    print("  format <type>  - Set output format (json/formatted/detailed)")
    print("  file <path>    - Process CSV file")
    print()
    
    current_format = 'formatted'
    
    while True:
        try:
            user_input = input("🏠 Enter address: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'help':
                print("\nCommands:")
                print("  help     - Show this help")
                print("  stats    - Show database statistics") 
                print("  format <type>  - Set output format (json/formatted/detailed)")
                print("  file <path>    - Process CSV file")
                print("  quit     - Exit")
                continue
                
            elif user_input.lower() == 'stats':
                if processor.db_service:
                    stats = processor.db_service.get_database_stats()
                    print(f"\n📊 Database Statistics:")
                    print(f"   Total addresses: {stats['total_unique_addresses']}")
                    print(f"   Cache hit rate: {stats['cache_hit_rate']:.1f}%")
                else:
                    print("❌ Database not available")
                continue
                
            elif user_input.lower().startswith('format '):
                new_format = user_input[7:].strip()
                if new_format in ['json', 'formatted', 'detailed']:
                    current_format = new_format
                    print(f"📋 Format set to: {current_format}")
                else:
                    print("❌ Invalid format. Use: json, formatted, or detailed")
                continue
                
            elif user_input.lower().startswith('file '):
                csv_file = user_input[5:].strip()
                if os.path.exists(csv_file):
                    print(f"📁 Processing file: {csv_file}")
                    try:
                        output_file = processor.process_csv_file(csv_file)
                        print(f"✅ File processed! Output: {output_file}")
                    except Exception as e:
                        print(f"❌ Error processing file: {e}")
                else:
                    print(f"❌ File not found: {csv_file}")
                continue
                
            else:
                # Process the address
                result = processor.process_single_address_input(
                    user_input, 
                    None, 
                    current_format
                )
                
                print(f"\n📋 Result:")
                if current_format == 'formatted':
                    print(f"   Original: {result.get('original_address', 'N/A')}")
                    print(f"   Formatted: {result.get('formatted_address', 'N/A')}")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}")
                    print(f"   From cache: {result.get('from_cache', False)}")
                    print(f"   Status: {result.get('status', 'N/A')}")
                else:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                print()
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    interactive_mode()
