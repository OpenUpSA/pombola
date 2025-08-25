# Constituency Offices Import Guide - 2025

## ⚠️ PRODUCTION SAFETY

This guide is for updating constituency offices on a **production server**. Always:

1. **Test first** - Run with `--verbose` before `--commit`
2. **Backup database** before any `--commit` operations  
3. **Use the 2025 folder** to avoid conflicts with previous imports
4. **Check party names** - Script validates against known parties

## Overview

This 2025 import system follows established patterns from 2014, 2019, and 2022 imports. The constituency offices system works with JSON files, not CSV directly. You'll need to convert your CSV to the expected JSON format first, then use the Django management command to import/update the offices.

## Quick Start (Production Safe)

```bash
# Navigate to the 2025 directory
cd pombola/south_africa/data/constituencies_and_offices/source_data/2025/

# 1. Check your CSV columns first
python convert_csv_to_json.py your_offices.csv output.json --party DA --show-columns

# 2. Test conversion (shows preview, doesn't write file)
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA --dry-run

# 3. Convert CSV to JSON (with confirmation)
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA

# 4. Test the import (from project root - DRY RUN)
cd ../../../../../
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --verbose

# 5. Run the actual import (only after testing!)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --commit --verbose
```

## Step-by-Step Process

### 1. Prepare your CSV file - REQUIRED FORMAT

**Your CSV MUST use these exact column names (case-sensitive):**

| Column Name | Required | Description | Example |
|-------------|----------|-------------|---------|
| `Title` | ✅ Yes | Office name | "Cape Town Office" |
| `Party` | ✅ Yes | Political party | "DA", "EFF", "IFP" |
| `Type` | No | "office" or "area" | "office" (default) |
| `Province` | ✅ Yes | Province name | "Western Cape" |
| `Physical Address` | No | Physical address | "123 Main St, Cape Town" |
| `Postal Address` | No | Postal address | "PO Box 123, Cape Town" |
| `Location` | No | Location for geocoding | "Cape Town, Western Cape" |
| `Municipality` | No | Municipality name | "City of Cape Town" |
| `Email` | No | Office email | "office@da.org.za" |
| `Tel` | No | Office phone | "021 123 4567" |
| `Fax` | No | Office fax | "021 123 4568" |
| `Contact Person` | No | Contact person name | "John Smith" |
| `Contact Role` | No | Person's position | "Constituency Contact" |
| `Person Cell` | No | Person's cell number | "082 123 4567" |
| `Person Email` | No | Person's email | "john@da.org.za" |
| `Source URL` | No | Data source URL | "https://example.com" |
| `Source Note` | No | Source description | "DA offices 2025" |

**Example CSV format:**
```csv
Title,Party,Type,Province,Physical Address,Email,Tel,Contact Person,Contact Role
"Cape Town Office",DA,office,"Western Cape","123 Main St, Cape Town","office@da.org.za","021 123 4567","John Smith","Constituency Contact"
"Cape Town Office",DA,office,"Western Cape","123 Main St, Cape Town","office@da.org.za","021 123 4567","Jane Doe","Administrator"
"Stellenbosch Area",DA,area,"Western Cape","Stellenbosch Municipality","stellenbosch@da.org.za","021 234 5678","Bob Wilson","Coordinator"
```

**⚠️ Important:**
- Use these **exact column names** - the script will not try to guess
- If your CSV has different column names, **rename them to match this format**
- Required columns must have data, optional columns can be empty
- **Multiple contacts per office:** Create separate rows with identical office details but different contact information
- **Note:** The converter creates separate JSON entries for each row, but the update command will merge contacts for offices with the same name

### 2. Convert CSV to JSON

```bash
# Navigate to the 2025 directory
cd pombola/south_africa/data/constituencies_and_offices/source_data/2025/

# Check what columns your CSV has
python convert_csv_to_json.py your_offices.csv output.json --party DA --show-columns

# Test conversion (preview only)
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA --dry-run

# Convert the CSV to JSON (includes confirmation prompt)
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA --start-date 2025-01-01

# With province default (if not in CSV)
python convert_csv_to_json.py your_offices.csv constituency_offices.json --party DA --province "Western Cape"
```

### 3. Run the update command

```bash
# Navigate to the project root directory
cd ../../../../../

# Test run (doesn't actually update database)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --verbose

# Actual update (commits to database) - ONLY AFTER TESTING
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --commit --verbose

# Update with party-specific options
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --commit --party DA --search-office --verbose

# End old offices for a party (careful!)
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/constituency_offices.json --commit --party DA --end-old-offices --verbose
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
