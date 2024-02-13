# ZA Members' Interests Data

There are several files in this directory:

## DOCX scraper

The scraper currently scrapes `.docx` files.
To prepare the file:

1. Split the `PDF` into seperate files small enough to open in Google Docs. [PDF Arranger](https://github.com/pdfarranger/pdfarranger) works well 
2. Open the files in Google Docs and download each in `.docx` format
3. Store the these files in `./docx_files/`

Create an environment and install dependencies using
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the script with the necessary arguments, e.g.
```
python scrape_interests_docx.py --input ./docx_files/ --output ../2021.json --year 2021 --source https://static.pmg.org.za/Register_of_Members_Interests_2021.pdf
```

This will combine documents into a single HTML file `main_html_file.html`

Run the Jupyter script `membersinterest.ipynb` making sure to update the input file name. The output should be `register.json`

Copy `register.json` to the `members-interests` directory and rename it to the corresponding year

## Conversion script

    convert_to_import_json.py

This script takes the raw data and processes it to clean it up, to match the mp
to entries in the database and to put it in the format that the
`interests_register_import_from_json` management command expects. This script
is highly specific to the above JSON files and the MP entries in the database
at the time of writing (3 Dec 2013).

You can run the script like this:

    cd pombola/south_africa/data/members-interests/
    ./convert_to_import_json.py 2022.json > 2022_for_import.json

This will require a production or equivalent data for the persons table to filter against.
You can either run the script in prod or build a local database instance like so:

`dokku postgres:export pombola > dumpitydump.dump`

`pg_restore -U pombola -d pombola dumpitydumplol.dump`

When processing new data you may well need to add more entries to the
`slug_corrections` attribute. Change the `finding_slug_corrections` to `True`
to enable some code that'll help you do that. Change it back to False when done.

## Final importable data

    2010_for_import.json
    2011_for_import.json
    2012_for_import.json
    2013_for_import.json
    2014_for_import.json
    2015_for_import.json
    2016_for_import.json
    2017_for_import.json
    2018_for_import.json

This is the output of the above conversion script. It is committed for ease of
adding to the database, and as looking at the diffs is an easy way to see the
results of changes to the conversion script.

To load this data into the database, you can run the management command:
(if there are already some entries you should delete them all using the admin)

    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2010_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2011_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2012_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2013_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2014_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2015_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2016_for_import.json
    ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2017_for_import.json
