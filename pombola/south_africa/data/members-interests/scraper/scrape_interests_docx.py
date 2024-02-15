import argparse
import json
import os
import string
import re
import time
import logging
import mammoth

from bs4 import BeautifulSoup
import lxml.etree


class Logger():
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name

    def initialize_logger(self):
        logging.basicConfig(level=logging.INFO, filemode="a", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        logger = logging.getLogger(__name__)
        file_handler = logging.FileHandler(self.log_file_name)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def log(self, message):
        if self.verbose:
            print(message)


class InterestScraper(object):
    def __init__(self, args):
        self.input = args.input
        self.output = args.output
        self.year = args.year
        self.source = args.source
        # self.logger = Logger(args.log_file).initialize_logger()

    def strip_bold(self, text):
        if re.match('(?s)<b.*?>(.*?)</b>', text):
            return re.match('(?s)<b.*?>(.*?)</b>', text).group(1).strip()
        else:
            return text

    def replace_character_codes(self, el):
        """
            Take an lxml element, replace unicode character codes for hyphens
            and non breaking spaces and return a string with the replaced
            characters
        """
        return string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')


    def fix_known_mps_shares_overlap(self, html):
        """
        Fix known problem areas where the MP name overlap with the shares next section and does not correctly tableize it
        """

        html =  html.replace('<p><strong>4.5BAPELA KOPENG OBED AFRICAN NATIONAL CONGRESS SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.5 BAPELA KOPENG OBED ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.209 PILANE-MAJAKE MAKGATHATSO CHANA ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.209 PILANE-MAJAKE MAKGATHATSO CHANA ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>3.1HENDRICKS MOGAMAD GANIEF EBRAHIM AL JAMA-AH SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts)</strong></p>','<p><strong>3.1 HENDRICKS MOGAMAD GANIEF EBRAHIM AL JAMA-AH</strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.223 SISULU LINDIWE NONCEBA AFRICAN NATIONAL CONGRESS SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.223 SISULU LINDIWE NONCEBA ANC</strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.4BARA MBULELO RICHMOND DEMOCRATIC ALLIANCE SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>7.4 BARA MBULELO RICHMOND DA</strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.174 MUTHAMBI AZWIHANGWISI FAITH ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.174 MUTHAMBI AZWIHANGWISI FAITH ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.56 MASIPA NOKO PHINEAS DEMOCRATIC ALLIANCE SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts)</strong></p>','<p><strong>7.56 MASIPA NOKO PHINEAS DA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.86 TARABELLA-MARCHESI NOMSA INNOCENCIA DA SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>7.86 TARABELLA-MARCHESI NOMSA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.115 MASEKO-JELE NOMATHEMBA HENDRIETTA ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.115 MASEKO-JELE NOMATHEMBA HENDRIETTA ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>8.20 MASHABELA NGWANAMAKWETLE RENEILOE EFF SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>8.20 MASHABELA NGWANAMAKWETLE RENEILOE EFF </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.143 MKHWANAZI JABULILE CYNTHIA NIGHTINGALE ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.143 MKHWANAZI JABULILE CYNTHIA NIGHTINGALE ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.112 MAPISA-NQAKULA NOSIVIWE NOLUTHANDO ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.112 MAPISA-NQAKULA NOSIVIWE NOLUTHANDO ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.114 MAREKWA GOBONAMANG PRUDENCE ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.114 MAREKWA GOBONAMANG PRUDENCE ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html = html.replace(chr(252), 'u')

        html =  html.replace('<p><strong>7.41 Kruger Hendrik Christiaan Crafford Democratic Alliance SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts)</strong></p>','<p><strong>7.41 KRUGER HENDRIK CHRISTIAAN CRAFFORD DA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.92 WALTERS THOMAS CHARLES RAVENSCROFT DA SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>7.92 WALTERS THOMAS CHARLES RAVENSCROFT DA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.24 GONDWE MIMMY MARTHA DEMOCRATIC ALLIANCE SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>7.24 GONDWE MIMMY MARTHA DA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>4.96 MAKHUBELA -MASHELE LUSIZO SHARON ANC SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>','<p><strong>4.96 MAKHUBELA-MASHELE LUSIZO SHARON ANC </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')

        html =  html.replace('<p><strong>7.82 SPIES ELEANORE ROCHELLE JACQUELENE DA SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts)</strong></p>','<p><strong>7.82 SPIES ELEANORE ROCHELLE JACQUELENE DA </strong></p><p><strong>SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts) </strong></p>')






        
        return html
    

    def extract_content_from_document(self, doc_file_path):
        """ Extract content from a .docx file and return a (text, html) tuple.
        """
        filename = doc_file_path
        ext = os.path.splitext(filename)[1]
        if ext == '.docx':
            html = ""
            with open(filename, "rb") as f:
                html = mammoth.convert_to_html(f).value
            return html
        else:
            raise ValueError("Can only handle .docx files, but got %s" % ext)

    def read_and_merge_html(self, file_path):
        """
        Reads the contents of multiple small files and merges it into one big file.
        """
        # self.logger.info("Reading and merging html files from {}".format(file_path))
        # self.logger.info("Reading and merging html files from {}".format(file_path))
        main_html = ""

        files = os.listdir(file_path)
        files_dict = {f.split('-')[1].split('.')[0]: f for f in files}
        sorted_files = [files_dict[str(f)] for f in sorted([int(x) for x in files_dict.keys()])]
        processed_files = 0
        for file in sorted_files:
            if file.endswith(".docx"):
                processed_files += 1
                full_file_path = os.path.join(file_path, file)
                start_time = time.time()
                extracted_html = self.extract_content_from_document(full_file_path)
                end_time = time.time() - start_time
                main_html += extracted_html
                # self.logger.info("Read {} in {} seconds".format(full_file_path, end_time))
        # self.logger.info("Finished reading and merging html {} dir".format(processed_files))
        return main_html

    # @cachetools.func.ttl_cache(maxsize=100000, ttl=1000 * 6000)
    def get_soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    def clean_up_soup(self, soup):
        """
        Remove all the unwanted tags from the soup.
        """
        all_children = soup.findChildren(recursive=False)
        for child_tag in all_children:
            if child_tag.name == 'p':
                child_div = child_tag.findChild()
                if child_div and child_div.name == "img":
                    child_tag.decompose()

            

        return soup

    def parse_html_generated_from_doc(self, html):
        """
            Parse the HTML to get the text.
        """
       

        CATEGORIES = {
            "SHARES AND OTHER FINANCIAL INTERESTS (Family and other trusts)": "SHARES AND OTHER FINANCIAL INTERESTS",
            "REMUNERATED EMPLOYMENT OUTSIDE PARLIAMENT": "REMUNERATED EMPLOYMENT OUTSIDE PARLIAMENT",
            "DIRECTORSHIPS AND PARTNERSHIPS": "DIRECTORSHIP AND PARTNERSHIPS",
            "CONSULTANCIES OR RETAINERSHIPS": "CONSULTANCIES OR RETAINERSHIPS",
            "SPONSORSHIPS": "SPONSORSHIPS",
            "GIFTS AND HOSPITALITY": "GIFTS AND HOSPITALITY",
            "BENEFITS": "BENEFITS",
            "TRAVEL": "TRAVEL",
            "LAND AND PROPERTY": "LAND AND PROPERTY",
            "PENSIONS": "PENSIONS",
            "PUBLIC CONTRACTS AWARDED": "CONTRACTS",
            "TRUSTS": "TRUSTS"
        }

        """
        The following implementation of the parser is based on the state machine
        concept.

        The variables described below are used to keep track of the current state

        eg. in_table: True when we are in a table and helps identify the
        table continuation over a page break.
        """
        self.mps_count = 0
        self.mps_names = []
        all_mps_data = []
        single_mp_interests = {}
        self.data = []
        self.all_sections = {}
        in_table = False
        self.section = ''

        start_time = time.time()
        soup = self.get_soup(html)
        print("Parsing html took {} seconds".format(time.time() - start_time))
        cleaned_up_soup = self.clean_up_soup(soup)
        main_div = cleaned_up_soup
        if main_div is None:
            raise ValueError("Could not find main content div")
        table_headers = []
        category_entries = []
        for div in main_div.findChildren(recursive=False):
            div_text = str(div.get_text().strip())
            pattern = r'^\d+\.\d+'
            if bool(re.match(pattern, div_text)):
                # in 2020, the MP's name is in the div with the number example 1.2GALO MANDLENKOSI PHILLIP
                # This is the mp name
                strip_content_number = ''.join([i for i in div_text if not i.isdigit()]).replace('.', '')
                self.mp = ' '.join(strip_content_number.replace("\xe2\x80\x93", "-").split(' ')).replace(',', '').replace(' -', ',').strip()
                self.mps_count = self.mps_count + 1
                self.mps_names.append(self.mp)
                if self.mp not in single_mp_interests:
                    single_mp_interests[self.mp] = {}
            if div_text in CATEGORIES:
                # This is the section name
                self.section = CATEGORIES[div_text]
                in_table = False
                category_entries = []
            if div.name == 'table':
                if 'Surname' in div_text:
                    continue
                # check if a party name is also in text
                if any(s for s in ['EFF'] if s in div_text):
                    continue
                table = div

                # Table parsing is wrong - there are no TH tagsmp)
                if table is not None:
                    if in_table:
                        # table continuation over a page break found, process it
                        print('overlap')
                        table_tr = table.find_all('tr')
                        for tr in list(table_tr):
                            section_content = {}
                            for n, inner_tr in list(enumerate(tr.find_all('th'))):
                                if not n > len(table_headers) - 1:
                                    print(table_headers[n])
                                    section_content[table_headers[n]] = str(
                                        inner_tr.text.encode('utf-8').strip())
                            if any("nothing to disclose" in s.lower() for s in section_content.values()):
                                category_entries = "Nothing to disclose"
                            else:
                                category_entries.append(section_content)
                    else:
                        table_tr = table.find_all('tr')
                        table_headers = [el.text.encode('utf-8').strip() for el in list(table_tr)[
                            0].select('th')]
                        for tr in list(table_tr)[1:]:
                            section_content = {}
                            for n, inner_tr in list(enumerate(tr.find_all('th'))):
                                if not n > len(table_headers) - 1:
                                    section_content[table_headers[n]] = str(
                                        inner_tr.text.encode('utf-8').strip())
                            if any("nothing to disclose" in s.lower() for s in section_content.values()):
                                category_entries = "Nothing to disclose"
                            else:
                                category_entries.append(section_content)
                            print(category_entries)

                    if self.section not in single_mp_interests[self.mp]:
                        single_mp_interests[self.mp][self.section] = {}
                    single_mp_interests[self.mp][self.section] = category_entries
                    single_mp_interests[self.mp]["mp"] = self.mp
                in_table = True

        all_mps_data.append(single_mp_interests)
        for mp in all_mps_data[0]:
            self.data.append(all_mps_data[0][mp])

    def write_results(self):
        with open(self.output, 'w') as outfile:
            json.dump({
                'year': self.year,
                'date': '%s-12-31' % (self.year),
                'source': self.source,
                'register': self.data,
                "mps_count": self.mps_count
            },
                outfile, indent=1)

    def write_html_to_file(self, html_str):

       
        # html_str_fixed_headers = self.fix_table_headers(html_str)
        html_str_fixed = self.fix_known_mps_shares_overlap(html_str)

        

        with open("main_html_file.html", 'w') as outfile:
            outfile.write(html_str_fixed)
            # self.logger.info("Wrote html to %s" % self.output)

        return html_str_fixed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape member's interests from pdf file")
    parser.add_argument('--input', help='Pdf file to scrape')
    parser.add_argument('--output', help='File to write json results to')
    parser.add_argument('--year', help='Year we are scraping')
    parser.add_argument('--source', help='Source of pdf file')
    parser.add_argument('--print-font-ids',
                        help='Print the font ids used in the document')
    parser.add_argument('--log_file', help='File to write log messages to')

    args = parser.parse_args()

    scraper = InterestScraper(args)

    if (args.print_font_ids):
        scraper.print_font_ids()
        exit()

    # Read and parse the word doc
    master_html = scraper.read_and_merge_html(file_path="docx_files")
    # write master_html to file
    html_str_fixed = scraper.write_html_to_file(master_html)
    start_time = time.time()
    print("--- %s seconds ---" % (time.time() - start_time))
    scraper.parse_html_generated_from_doc(html_str_fixed)
    scraper.write_results()
