# Constituency Offices Import Guide

## Overview

The constituency offices system works with JSON files, not CSV directly. You'll need to convert your CSV to the expected JSON format first, then use the Django management command to import/update the offices.

## Quick Start

```bash
# Navigate to the constituencies_and_offices directory
cd pombola/south_africa/data/constituencies_and_offices/

# 1. Check your CSV columns
python convert_csv_to_json.py your_offices.csv output.json --party DA --show-columns

# 2. Convert CSV to JSON
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA

# 3. Test the import (from project root)
cd ../../../../
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --verbose

# 4. Run the actual import
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --commit --verbose
```

## Step-by-Step Process

### 1. Prepare your CSV file

Your CSV should have columns like:
- `Title` or `Name` - Office name
- `Party` - Political party slug (e.g., DA, EFF, ANC)
- `Type` - Either "office" or "area"
- `Province` - Province name
- `Physical_Address` or `Physical Address` - Physical address
- `Postal_Address` or `Postal Address` - Postal address  
- `Location` - Location for geocoding
- `Municipality` - Municipality name
- `Email` or `E-mail` - Office email
- `Tel` or `Phone` - Office phone
- `Fax` - Office fax
- `Person_Name` or `Person Name` - Contact person name
- `Person_Position` or `Person Position` - Person's position
- `Person_Cell` or `Person Cell` - Person's cell number
- `Person_Email` or `Person Email` - Person's email
- `Source_URL` or `Source URL` - Data source URL
- `Source_Note` or `Source Note` - Source description

### 2. Convert CSV to JSON

```bash
# Navigate to the constituencies_and_offices directory
cd pombola/south_africa/data/constituencies_and_offices/

# First, check what columns your CSV has
python convert_csv_to_json.py your_offices.csv output.json --party DA --show-columns

# Convert the CSV to JSON
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA --start-date 2025-01-01
```

### 3. Run the update command

```bash
# Navigate to the project root directory
cd /path/to/pombola/

# Test run (doesn't actually update database)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --verbose

# Actual update (commits to database)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --commit --verbose

# Update with party-specific options
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --commit --party DA --search-office --verbose

# End old offices for a party (careful!)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/constituency_offices.json --commit --party DA --end-old-offices --verbose
```

## Command Options

- `--commit` - Actually update the database (without this, it's a dry run)
- `--verbose` - Show detailed output
- `--party PARTY_NAME` - Specify party (e.g., DA, EFF, ANC)
- `--search-office` - Search for similar office names if exact match not found
- `--end-old-offices` - End offices for the party that aren't in the import file

## How the Update Logic Works

1. **Office Matching**: Tries to find existing offices by:
   - Exact name match (case-insensitive)
   - Identifier scheme matches
   - Similar names (if `--search-office` is used)

2. **Updates existing offices**:
   - Updates name if different
   - Sets end date to "future" if currently ended
   - Updates contact information
   - Updates location/address information

3. **Creates new offices** if no match found

4. **People management**:
   - Matches people by name using various methods
   - Creates positions linking people to offices
   - Updates contact information (phone, email)
   - Validates that "Constituency Contact" people are current MPs/MPLs

5. **Ending old offices**: If `--end-old-offices` is used, offices for the party that aren't in the import file will be ended

## Important Notes

- **Always test first**: Run without `--commit` to see what would happen
- **Backup your database** before running with `--commit`
- **People matching is fuzzy**: The system tries various methods to match people names
- **Geocoding happens automatically**: Addresses are geocoded for mapping
- **Validation**: The system validates that constituency contacts are actual MPs/MPLs

## Troubleshooting

### People not found
- Check the log file `missing_or_unmatched_people.log`
- Names need to match existing Person records in the database
- Consider adding alternative names to Person records

### Locations not found
- Check the verbose output for geocoding failures
- Consider improving address formatting
- Manual coordinates can be added with `manual_lonlat` field

### Parties not found
- Ensure the party exists in the database with the correct slug
- Party names are case-sensitive and should match existing Organisation records

## Example JSON Structure

```json
{
  "offices": [
    {
      "Title": "DA Constituency Office: Cape Town",
      "Party": "DA",
      "Type": "office",
      "Province": "Western Cape",
      "Physical Address": "123 Main Street, Cape Town, Western Cape",
      "Postal Address": "PO Box 123, Cape Town, 8000",
      "Location": "Cape Town, Western Cape",
      "Municipality": "City of Cape Town",
      "E-mail": "capetown@da.org.za",
      "Tel": "021 123 4567",
      "Source URL": "https://example.com/source",
      "Source Note": "DA office data 2025",
      "People": [
        {
          "Name": "John Smith",
          "Position": "Constituency Contact",
          "Cell": "082 123 4567",
          "Email": "john.smith@da.org.za"
        }
      ]
    }
  ],
  "start_date": "2025-01-01",
  "end_date": "future"
}
```
