# 2025 Constituency Offices - Production Ready Setup

## Summary

✅ **Files are now safely organized in `source_data/2025/` folder**
✅ **Production-safe conversion script with validation and backups**
✅ **Follows established patterns from 2014, 2019, 2022**
✅ **No conflicts with existing import tools**

## File Structure

```
pombola/south_africa/data/constituencies_and_offices/
├── source_data/
│   ├── 2025/                           # NEW - 2025 import tools
│   │   ├── README.md                   # 2025-specific documentation
│   │   ├── CONSTITUENCY_OFFICES_IMPORT_GUIDE.md  # Complete guide
│   │   ├── convert_csv_to_json.py      # Enhanced converter script
│   │   ├── csv/                        # Put your CSV files here
│   │   │   └── test-da.csv            # Example CSV
│   │   └── *.json                      # Generated JSON files
│   ├── 2022/                           # Previous year
│   ├── 2019/                           # Previous year
│   ├── 2014/                           # Previous year
│   ├── convert_to_import_json.py       # Previous conversion script
│   └── office_workbook.ipynb          # Previous Jupyter workflow
├── README.md                           # Main documentation (unchanged)
├── all_constituencies.csv             # Historical data
└── new-in-issue-1115-data.csv        # Historical data
```

## Production Workflow

### 1. Prepare your data
```bash
cd pombola/south_africa/data/constituencies_and_offices/source_data/2025/
# Put your CSV file in csv/ folder
```

### 2. Test and convert
```bash
# Check CSV structure
python convert_csv_to_json.py csv/your-file.csv output.json --party PARTY --show-columns

# Test conversion (no files written)
python convert_csv_to_json.py csv/your-file.csv output.json --party PARTY --dry-run

# Convert for real (includes confirmation)
python convert_csv_to_json.py csv/your-file.csv output.json --party PARTY
```

### 3. Import to database
```bash
cd ../../../../../  # Back to project root

# TEST FIRST - dry run
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/output.json --verbose

# Only after testing - commit to database
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/output.json --commit --verbose
```

## Safety Features

1. **Party validation** - Validates against known parties (ANC, DA, EFF, IFP, etc.)
2. **Preview mode** - Shows exactly what will be created before writing
3. **Confirmation prompts** - Requires user confirmation before writing files
4. **Automatic backups** - Creates timestamped backups of existing files
5. **Error handling** - Continues processing if individual rows fail
6. **Dry run mode** - Test conversions without writing any files
7. **Strict format requirements** - Uses exact column names, no guessing

## Known Parties

The script validates against these known parties:
- ANC, DA, EFF, IFP, FF, ACDP, ATM, MF, COPE, UDM, PAC, AZAPO

## Required CSV Format

**Your CSV MUST use these exact column names:**

```csv
Title,Party,Type,Province,Physical Address,Email,Tel,Contact Person,Contact Role
"Cape Town Office",DA,office,"Western Cape","123 Main St, Cape Town","office@da.org.za","021 123 4567","John Smith","Constituency Contact"
"Cape Town Office",DA,office,"Western Cape","123 Main St, Cape Town","office@da.org.za","021 123 4567","Jane Doe","Administrator"
"Stellenbosch Office",DA,office,"Western Cape","456 Wine St, Stellenbosch","stellenbosch@da.org.za","021 234 5678","Bob Wilson","Coordinator"
```

**Required columns:** `Title`, `Party`, `Province`
**Optional columns:** All others (can be empty but headers must exist)

**Multiple contacts per office:** Use separate rows with identical office details but different contact information.

⚠️ **No flexible column mapping** - Use these exact names or rename your columns to match.

## Tested and Ready

✅ Script tested with sample data
✅ Help system working
✅ Dry-run functionality working  
✅ Column detection working
✅ Preview system working
✅ Safety prompts working

**Ready for production use!**
