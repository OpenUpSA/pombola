# ZA Members' Interests Data

## Prepping and importing member's interests

Importing member's interests is a multistep process.

### Obtain register PDF

Get the latest register `PDF` from [parliament](https://www.parliament.gov.za/register-members-Interests).

### Trim PDF

Use [PDF Arranger](https://github.com/pdfarranger/pdfarranger) to remove cover and contents pages to have a final `PDF` that is just the register.

### Convert PDF to DOCX

Previously we used `Google Docs` to convert the `PDF` to `DOCX`. This was very cumbersome and meant working in batches of 80 pages at a time.
A workable and faster third-party solution is [ilovepdf.com](https://www.ilovepdf.com/pdf_to_word).

### Convert DOCX to HTML

Create an environment and install dependencies in the `./pombola/south_africa/data/members-interests/scraper` directory:
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Use the first cell of `./scraper/docx_to_html_to_json.ipynb` to convert the `DOCX` to `HTML` with Mammoth.

### Convert to JSON

Run the other cells in the notebook to convert it to a workable `json` file.

### Copy to server

The next steps need to be run on the server as it uses the production database.

### Convert to importable json file

```
cd pombola/south_africa/data/members-interests/
./convert_to_import_json.py 2024.json > 2024_for_import.json
```

When processing new data you may well need to add more entries to the
`slug_corrections` attribute. Change the `finding_slug_corrections` to `True`
to enable some code that'll help you do that. Change it back to False when done.

### Import final json file

To load this data into the database, you can run the management command:
(if there are already some entries you should delete them all using the admin)

```
./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2024_for_import.json
```

## Some useful notes for possible issues

- name, surname and title orders may change from year to year. Please see 
`/pombola/south_africa/data/members-interests/convert_to_import_json.py` lines 1325 and 1328 to tweak this if need be: `name_ordered = re.sub(r'^(\w+\b\s+\w+\b)\s+(.*)$', r'\2 \1', name_only)` where `\2 \1` determines the order.

- If the list of missing slugs is long, export existing slugs from Metbase and use ChatGPT to suggest matches. Confirm with PMG before importing.

- Section names might change, this would need to be changed in the convert script to match the `json` file.

- Regex patterns might also change and if there are broken entries or overlaps in the `json` file, make sure the patterns and sections are correct.