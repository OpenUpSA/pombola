import json
import logging

import pandas as pd


# constants
PROVINCE_LIST = ['Mpumalanga', 'Northern Cape', 'Western Cape', 'Free State']
JSON_OUTPUT_FILE_NAME = 'anc_constituency_offices.json'


def extract_excel_file_data(logger, file_name):
    excel_file = file_name
    xls = pd.ExcelFile(excel_file)
    logger.info('Extracted data from excel file: {}'.format(excel_file))
    return xls


def clean_up_data_point(data_point):
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
    all_offices = []
    for sheet_name in sheet_names:
        if sheet_name in PROVINCE_LIST:
            df1 = pd.read_excel(xls, sheet_name)
            logger.info('Processing sheet: {}'.format(sheet_name))
            row_count = 0
            for row in df1.itertuples():
                if row.Index <= 0:
                    continue
                name = clean_up_data_point(row[1])
                role = clean_up_data_point(row[2])
                province = clean_up_data_point(row[3])
                city = clean_up_data_point(row[4])
                address = clean_up_data_point(row[5])
                email = clean_up_data_point(row[6])
                telephone = clean_up_data_point(row[7])
                office_admin_name = clean_up_data_point(row[8])
                office_admin_telephone = clean_up_data_point(row[9])
                office_admin_email = clean_up_data_point(row[10])
                office_admin_alternative_telephone = clean_up_data_point(row[11])
                alternative_email = clean_up_data_point(row[12])
                party = clean_up_data_point(row[13])
                office_unique_identifier = ''
                if city:
                    office_unique_identifier = city
                elif province:
                    office_unique_identifier = province
                else:
                    office_unique_identifier = row.Index
                office_title = "ANC Constituency Office {0}".format(
                    office_unique_identifier)
                output = {
                    "Province": province,
                    "Fax": "",
                    "identifiers": {
                        "constituency-office/ANC/": ""
                    },
                    "Tel": telephone,
                    "Title": office_title,
                    "People": [
                        {
                            "Cell": office_admin_telephone,
                            "Position": "Office Admin",
                            "Name": office_admin_name
                        },
                        {
                            "Cell": office_admin_alternative_telephone,
                            "Position": "Office Admin",
                            "Name": office_admin_name
                        },
                        {
                            "cell": telephone,
                            "Position": role,
                            "Name": name
                        }
                    ],
                    "E-Mail": email,
                    "Source URL": "",
                    "Party": party,
                    "Ward": "",
                    "Postal Address": address,
                    "Type": "office",
                    "Source Note": "ANC {} Constituency List 2021".format(city),
                    "Physical Address": address
                }
                all_offices.append(output)
                row_count += 1
            logger.info('Processed {} rows for sheet: {}'.format(
                row_count, sheet_name))
            write_to_json(logger, JSON_OUTPUT_FILE_NAME, all_offices)


def create_logger(log_file_name):
    logging.basicConfig(level=logging.INFO, filemode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


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
        logger, 'Updated ANC Constituency Office for Open Up to add.xlsx')
    process_rows(logger, xls)
