#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

./manage.py pombola_sayit_sync_pombola_to_popolo
./manage.py popolo_name_resolver_init

./manage.py za_hansard_check_for_new_sources
./manage.py za_hansard_run_parsing
./manage.py za_hansard_load_into_sayit

# Run the ZA Hansard questions importer (all steps)
./manage.py za_hansard_q_and_a_scraper --run-all-steps

# Run the committee minutes scraper and imports
./manage.py za_hansard_pmg_api_scraper --scrape --save-json --import-to-sayit --delete-existing --commit
