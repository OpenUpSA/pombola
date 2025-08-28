#!/usr/bin/env python3
"""
Convert constituency offices CSV to JSON format for the 2025 update.

This script follows the established patterns from previous imports (2014, 2019, 2022)
and includes safety checks for production use.

Usage:
    python convert_csv_to_json.py input.csv output.json --party PARTY_NAME

Expected CSV columns (flexible - script will show available columns):
- Title/Name/Office_Name: Office name
- Party/Political_Party: Political party
- Type: 'office' or 'area'  
- Province: Province name
- Physical_Address: Physical address
- Postal_Address: Postal address
- Location: Location for geocoding
- Municipality: Municipality name
- Email/E-mail: Office email
- Tel/Phone/Contact_Number: Office phone
- Fax: Office fax
- Contact_Person/Person_Name: Contact person name
- Contact_Role/Person_Position: Person's position
- Person_Cell: Person's cell number
- Person_Email: Person's email
- Source_URL: Data source URL
- Source_Note: Source description

Safety Features:
- Validates party names against known parties
- Shows preview before writing file
- Creates backup of existing files
- Validates required fields
"""

import csv
import json
import argparse
import sys
import os
import shutil
from datetime import datetime

# Known valid party slugs (based on existing data)
KNOWN_PARTIES = {
    'ANC': 'anc',
    'DA': 'da', 
    'EFF': 'eff',
    'IFP': 'ifp',
    'FF': 'ff',
    'ACDP': 'acdp',
    'ATM': 'atm',
    'MF': 'mf',
    'COPE': 'cope',
    'UDM': 'udm',
    'PAC': 'pac',
    'AZAPO': 'azapo',
    'GOOD': 'good',
    'NCC': 'ncc',
    'RISE': 'rise',
}

def validate_party(party_name):
    """Validate party name against known parties."""
    party_upper = party_name.upper()
    if party_upper in KNOWN_PARTIES:
        return KNOWN_PARTIES[party_upper]
    
    print(f"WARNING: Unknown party '{party_name}'")
    print("Known parties:", ", ".join(KNOWN_PARTIES.keys()))
    response = input("Continue anyway? (y/N): ")
    if response.lower() != 'y':
        sys.exit(1)
    return party_name.lower()

def backup_existing_file(filepath):
    """Create backup of existing file."""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"Created backup: {backup_path}")

def show_preview(data, num_offices=3):
    """Show preview of converted data."""
    print(f"\n=== PREVIEW: {len(data['offices'])} offices to be created ===")
    for i, office in enumerate(data['offices'][:num_offices]):
        print(f"\nOffice {i+1}:")
        print(f"  Title: {office['Title']}")
        print(f"  Party: {office['Party']}")
        print(f"  Type: {office['Type']}")
        if 'Province' in office:
            print(f"  Province: {office['Province']}")
        if 'Physical Address' in office:
            print(f"  Address: {office['Physical Address'][:50]}...")
        if 'People' in office:
            print(f"  People: {len(office['People'])} person(s)")
            for person in office['People']:
                print(f"    - {person['Name']} ({person.get('Position', 'No position')})")
    
    if len(data['offices']) > num_offices:
        print(f"\n... and {len(data['offices']) - num_offices} more offices")
    
    print(f"\nStart date: {data['start_date']}")
    print(f"End date: {data['end_date']}")
    print("="*50)

def convert_csv_to_json(csv_file, json_file, party_name, start_date, end_date, province=None, dry_run=False):
    """Convert CSV file to JSON format expected by the update command."""
    
    # Validate party
    party_slug = validate_party(party_name)
    
    offices = []
    errors = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Print available columns for debugging
        print("Available CSV columns:")
        for i, col in enumerate(reader.fieldnames):
            print(f"  {i}: {col}")
        print()
        
        for row_num, row in enumerate(reader, 1):
            try:
                office = {}
                
                # Required fields with multiple possible column names
                title_options = ['Title', 'Name', 'Office_Name', 'Office Name']
                title = None
                for opt in title_options:
                    if row.get(opt):
                        title = row.get(opt).strip()
                        break
                
                if not title:
                    title = f'{party_name} Office {row_num}'
                
                # Format title consistently (following office_workbook pattern)
                if not title.startswith(party_name):
                    office['Title'] = f"{party_name} Constituency Office: {title}"
                else:
                    office['Title'] = title
                
                # Party and type
                office['Party'] = row.get('Party', row.get('Political_Party', party_name)).strip()
                office['Type'] = row.get('Type', 'office').strip().lower()
                
                # Province (with fallback to command line argument)
                office_province = row.get('Province', province)
                if office_province:
                    office['Province'] = office_province.strip()
                
                # Optional location fields
                address_options = ['Physical_Address', 'Physical Address', 'Address']
                for opt in address_options:
                    if row.get(opt):
                        office['Physical Address'] = row.get(opt).strip()
                        break
                
                postal_options = ['Postal_Address', 'Postal Address']
                for opt in postal_options:
                    if row.get(opt):
                        office['Postal Address'] = row.get(opt).strip()
                        break
                
                if row.get('Location'):
                    office['Location'] = row.get('Location').strip()
                if row.get('Municipality'):
                    office['Municipality'] = row.get('Municipality').strip()
                
                # Contact fields (multiple possible column names)
                email_options = ['Email', 'E-mail', 'E_mail']
                for opt in email_options:
                    if row.get(opt):
                        office['E-mail'] = row.get(opt).strip()
                        break
                
                phone_options = ['Tel', 'Phone', 'Contact_Number', 'Contact Number']
                for opt in phone_options:
                    if row.get(opt):
                        office['Tel'] = row.get(opt).strip()
                        break
                
                if row.get('Fax'):
                    office['Fax'] = row.get('Fax').strip()
                
                # Source information
                office['Source URL'] = row.get('Source_URL', row.get('Source URL', 'CSV import 2025')).strip()
                office['Source Note'] = row.get('Source_Note', row.get('Source Note', f'Imported from CSV on {datetime.now().strftime("%Y-%m-%d")}')).strip()
                
                # People associated with office (following office_workbook pattern)
                people = []
                person_name_options = ['Contact_Person', 'Contact Person', 'Person_Name', 'Person Name']
                person_name = None
                for opt in person_name_options:
                    if row.get(opt):
                        person_name = row.get(opt).strip()
                        break
                
                if person_name:
                    person = {'Name': person_name}
                    
                    # Position/Role
                    position_options = ['Contact_Role', 'Contact Role', 'Person_Position', 'Person Position', 'Position']
                    for opt in position_options:
                        if row.get(opt):
                            person['Position'] = row.get(opt).strip()
                            break
                    
                    # Person contact details
                    if row.get('Person_Cell', row.get('Person Cell')):
                        person['Cell'] = row.get('Person_Cell', row.get('Person Cell')).strip()
                    
                    person_email_options = ['Person_Email', 'Person Email']
                    for opt in person_email_options:
                        if row.get(opt):
                            person['Email'] = row.get(opt).strip()
                            break
                    
                    # If no person email, use office email
                    if 'Email' not in person and 'E-mail' in office:
                        person['Email'] = office['E-mail']
                    
                    # If no person phone, use office phone  
                    if 'Cell' not in person and 'Tel' in office:
                        person['Tel'] = office['Tel']
                    
                    if row.get('Person_Alt_Name', row.get('Person Alt Name')):
                        person['Alternative Name'] = row.get('Person_Alt_Name', row.get('Person Alt Name')).strip()
                    
                    people.append(person)
                
                if people:
                    office['People'] = people
                
                # Add identifiers for tracking (following office_workbook pattern)
                office['identifiers'] = {
                    f"constituency-office/{party_slug}/": f"{party_slug}-{row_num}"
                }
                
                offices.append(office)
                print(f"✓ Processed row {row_num}: {office['Title']}")
                
            except Exception as e:
                error_msg = f"Error processing row {row_num}: {e}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
                print(f"  Row data: {dict(row)}")
                continue
    
    # Show errors summary
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    # Create the final JSON structure
    data = {
        'offices': offices,
        'start_date': start_date,
        'end_date': end_date
    }
    
    # Show preview
    show_preview(data)
    
    # Confirm before writing
    if len(offices) == 0:
        print("❌ No offices to convert!")
        return False
    
    if dry_run:
        print(f"\n🔍 DRY RUN: Would write {len(offices)} offices to {json_file}")
        return True
    
    response = input(f"\nProceed to write {len(offices)} offices to {json_file}? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return False
    
    # Backup existing file
    backup_existing_file(json_file)
    
    # Write to JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Conversion complete!")
    print(f"Converted {len(offices)} offices to {json_file}")
    print(f"Party: {party_name} (slug: {party_slug})")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} rows had errors and were skipped")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Convert constituency offices CSV to JSON for 2025 update',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show CSV columns
  python convert_csv_to_json.py offices.csv output.json --party DA --show-columns
  
  # Convert DA offices
  python convert_csv_to_json.py da-offices.csv da-offices.json --party DA --province "Western Cape"
  
  # Convert with custom dates
  python convert_csv_to_json.py offices.csv offices.json --party EFF --start-date 2025-02-01 --end-date 2030-01-31
        """)
    
    parser.add_argument('csv_file', help='Input CSV file path')
    parser.add_argument('json_file', help='Output JSON file path')
    parser.add_argument('--party', required=True, 
                       help='Party name (e.g., DA, EFF, ANC, IFP)')
    parser.add_argument('--province', 
                       help='Default province if not specified in CSV')
    parser.add_argument('--start-date', default='2025-01-01', 
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='future', 
                       help='End date (YYYY-MM-DD or "future")')
    parser.add_argument('--show-columns', action='store_true', 
                       help='Show CSV columns and exit')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show preview without writing file')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)
    
    if args.show_columns:
        with open(args.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print("Available CSV columns:")
            for i, col in enumerate(reader.fieldnames):
                print(f"  {i}: {col}")
            
            # Show a sample row
            try:
                sample_row = next(reader)
                print(f"\nSample data (first row):")
                for col, value in sample_row.items():
                    if value:  # Only show non-empty values
                        print(f"  {col}: {value[:50]}")
            except StopIteration:
                print("\n(No data rows found)")
        return
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be written")
    
    success = convert_csv_to_json(
        args.csv_file, 
        args.json_file, 
        args.party, 
        args.start_date, 
        args.end_date,
        args.province,
        args.dry_run
    )
    
    if success and not args.dry_run:
        print(f"\n📁 File created: {args.json_file}")
        print(f"📁 Ready for: python manage.py south_africa_update_constituency_offices {args.json_file}")
        print("\n⚠️  IMPORTANT: Test with --verbose flag first before using --commit!")
    elif args.dry_run:
        print("\n🔍 Dry run complete - no files were written")

if __name__ == '__main__':
    main()
