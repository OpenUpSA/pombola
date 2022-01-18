import json
import logging

import pandas as pd


# constants
JSON_OUTPUT_FILE_NAME = 'pombola/south_africa/data/constituencies_and_offices/source_data/2021/anc/anc-2021-data.json'


def extract_excel_file_data(logger, file_name):
    excel_file = file_name
    xls = pd.ExcelFile(excel_file)
    logger.info('Extracted data from excel file: {}'.format(excel_file))
    return xls


def clean_up_data_point(data_point):
    # check if data_point is a float and a nan
    import math
    if isinstance(data_point, float):
        if math.isnan(data_point):
            data_point = ''
        else:
            data_point = str(int(data_point))
    if isinstance(data_point, int):
        data_point = str(data_point)
    data_point_without_isnan = '' if data_point != data_point else data_point
    data_point = data_point_without_isnan.replace('\n', ' ').replace('\r', '')
    # utf encoding
    data_point = data_point.encode('utf-8')
    return data_point


def write_to_json(logger, json_file_name, all_offices):
    with open(json_file_name, 'w') as outfile:
        json.dump(all_offices, outfile)
    logger.info('Wrote to json file: {}'.format(json_file_name))


def process_rows(logger, xls):
    sheet_names = xls.sheet_names
    logger.info('Found {} sheets for processing: {}'.format(
        len(sheet_names), sheet_names))
    all_offices = {
        "offices": [],
        "start_date": "2021-11-01",
        "end_date": "2021-11-31"
    }
    track_offices = {}
    entries_count = 0
    for sheet_name in sheet_names:
        df1 = pd.read_excel(xls, sheet_name)
        logger.info('Processing sheet: {}'.format(sheet_name))
        row_count = 0
        for row in df1.itertuples():
            if row.Index < 0:
                continue
            office_name = clean_up_data_point(row[1])
            postal_address = clean_up_data_point(row[2])
            office_contact_name = clean_up_data_point(row[3])
            office_contact_role = clean_up_data_point(row[4])
            office_contact_telephone = clean_up_data_point(row[5])
            office_contact_email = clean_up_data_point(row[6])
            party = clean_up_data_point(row[7])
            province = sheet_name


            office_unique_identifier = ''

            if province:
                office_unique_identifier = province
            else:
                office_unique_identifier = row.Index
            office_title = "{0} Constituency Office {1} {2}".format(
                party, office_unique_identifier, office_name)

            if office_contact_name:
                office_admin1 = {
                        "Tel": office_contact_telephone,
                        "Name": office_contact_name,
                        "Email": office_contact_email,
                        "Position": office_contact_role
                    }

            if track_offices.get(office_title):
                already_added_office = track_offices.get(office_title)[0]
                if already_added_office['Title'] == office_title:
                    # check if address is same
                    if already_added_office['Physical Address'] == postal_address:
                        already_added_office['People'].append(office_admin1)
                        continue
                    else:
                        import random
                        rand_int = random.randint(0, 99)
                        already_added_office['Title'] = already_added_office['Title'] + \
                            " " + str(rand_int)
            else:
                output = {
                    "Province": province,
                    "Postal Address": postal_address,
                    "Physical Address": postal_address,
                    "Title": office_title,
                    "Party": party,
                    "Type": "office",
                    "Source URL": "https://www.pa.org.za/media_root/file_archive/ANC_Constituency_Offices_2021.xlsx",
                    "Source Note": "ACDP Constituency Offices 2021",
                    "People": []
                }
                track_offices[office_title] = [output]
                output['People'].append(office_admin1)
                all_offices['offices'].append(output)
            row_count += 1
            entries_count += 1
        logger.info('Processed {} rows for sheet: {}'.format(
            row_count, sheet_name))
        write_to_json(logger, JSON_OUTPUT_FILE_NAME, all_offices)
    logger.info("processed {} entries from excel".format(entries_count))
    return entries_count


def create_logger(log_file_name):
    logging.basicConfig(level=logging.INFO, filemode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def verify_json_entries(logger, rows_processed, json_file_name):
    data_len = 0
    with open(json_file_name, 'r') as json_file:
        json_data = json.load(json_file)
        # loop through json data
        for _ in json_data['offices']:
            data_len += 1
        # append extra json fields like title, start_date and end_date
    logger.info('Verified json file: {} has {} entries out of the {} rows ingested'.format(
        json_file_name, data_len, rows_processed))


if __name__ == '__main__':
    """
        This script will extract the data from the excel file and write it to a json file.
        Example command to load data after running this script:

        docker-compose run --rm app ./manage.py \
        south_africa_update_constituency_offices --verbose \
        anc_constituency_offices.json --party ANC --commit --end-old-offices
    """
    logger = create_logger('file.log')
    xls = extract_excel_file_data(
        logger, 'Standard Template for constituency members info.xlsx')
    rows_processed = process_rows(logger, xls)

    verify_json_entries(logger, rows_processed, JSON_OUTPUT_FILE_NAME)
