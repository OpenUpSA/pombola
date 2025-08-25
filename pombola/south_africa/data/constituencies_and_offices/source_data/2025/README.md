# 2025 Constituency Offices Import

This folder contains tools and data for importing constituency office data in 2025, following the established patterns from previous years (2014, 2019, 2022).

## Files

- `convert_csv_to_json.py` - Enhanced CSV to JSON converter with safety features
- `CONSTITUENCY_OFFICES_IMPORT_GUIDE.md` - Complete import documentation
- `csv/` - Place your source CSV files here
- `*.json` - Generated JSON files ready for import

## Safety Features

The 2025 tools include several safety improvements:

- **Party validation** - Validates against known party slugs
- **Preview mode** - Shows what will be converted before writing files
- **Backup creation** - Automatically backs up existing files
- **Confirmation prompts** - Requires confirmation before writing
- **Dry run mode** - Test conversions without writing files
- **Error handling** - Continues processing if some rows fail
- **Flexible column mapping** - Handles various CSV column name formats

## Quick Usage

```bash
# Check CSV structure
python convert_csv_to_json.py your-offices.csv output.json --party DA --show-columns

# Test conversion (preview only)
python convert_csv_to_json.py your-offices.csv da-offices.json --party DA --dry-run

# Convert for real
python convert_csv_to_json.py your-offices.csv da-offices.json --party DA

# Import (from project root)
cd ../../../../../
python manage.py south_africa_update_constituency_offices pombola/south_africa/data/constituencies_and_offices/source_data/2025/da-offices.json --verbose
```

## File Naming Convention

Follow the pattern from previous years:
- `[province]-[party].csv` for source files (e.g., `western-cape-da.csv`)
- `[province]-[party].json` for converted files (e.g., `western-cape-da.json`)

## Previous Years Reference

- `../2022/` - 2022 import files
- `../2019/` - 2019 import files  
- `../2014/` - 2014 import files
- `../convert_to_import_json.py` - Previous conversion script
- `../office_workbook.ipynb` - Previous Jupyter notebook workflow

The 2025 tools incorporate lessons learned from all previous imports.
