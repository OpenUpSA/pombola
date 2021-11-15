import argparse
import json
import os
import pprint
import string
import re
import time
import logging

import cachetools.func

import mammoth
import scraperwiki

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
        self.logger = Logger(args.log_file).initialize_logger()

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

    def scrape_pdf(self):

        pdfdata = open(self.input, 'r').read()
        xmldata = scraperwiki.pdftoxml(pdfdata)

        self.data = []
        namecount = 0
        sectioncount = -1
        intable = False
        currentsection = ''
        count = 0

        # Fontspecs are used to determine what content we're looking at.
        # These ids appear in the first content page when parsing the document.
        # Some years have more and different ids than others.
        # Setting the correct values is a trial and error apporach.
        # These ids can be obtained by running:
        # `./scrape_interests_pdf.py --input <filename>.pdf --print-font-ids=True`

        font_id_1 = '3'
        font_id_2 = '4'
        font_id_3 = '5'

        root = lxml.etree.fromstring(xmldata.encode('utf8'))
        pages = list(root)

        for page in pages:
            for el in list(page):
                element_text = ''
                count = count + 1
                if el.tag == "text":
                    text_element = self.strip_bold(re.match(
                        '(?s)<text.*?>(.*?)</text>', self.replace_character_codes(el)).group(1))
                    if el.attrib['font'] == font_id_1:
                        # found a new MP
                        if len(self.data) == namecount:
                            self.data.append({})

                        self.data[namecount]['mp'] = text_element
                        namecount = namecount + 1

                    elif el.attrib['font'] == font_id_2 and re.match('[0-9]+[.] ([A-Z]+)', text_element):

                        # found new section
                        if text_element == '1. SHARES AND OTHER FINANCIAL INTERESTS':
                            sectioncount = sectioncount + 1
                        intable = False

                        currentsection = re.match(
                            '[0-9]{1,2}[.] (.*)', text_element).group(1)
                        self.data[namecount-1][currentsection] = {}

                    elif currentsection != '':
                        if text_element == 'Nothing to disclose.':
                            self.data[namecount -
                                      1][currentsection] = text_element
                        elif not intable and el.attrib['font'] == font_id_3:
                            curtable = {}
                            intable = True
                            haverows = False
                            curtable[el.attrib['left']] = text_element
                            self.data[namecount-1][currentsection] = []
                            self.data[namecount-1][currentsection].append({})
                        elif intable and not haverows and text_element == ' ':
                            haverows = True
                        # Check this: we've stripped off the bold element
                        elif intable and not haverows and not re.match('(?s)<b.*?>(.*?)</b>', text_element) and el.attrib['font'] == font_id_3:
                            haverows = True
                        elif intable and not haverows:
                            curtable[el.attrib['left']] = text_element
                        elif intable and haverows and text_element == ' ':
                            if len(self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1]) > 0:
                                self.data[namecount -
                                          1][currentsection].append({})
                        elif intable and haverows:
                            if curtable[el.attrib['left']] in self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1]:
                                if self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]][-1] == ' ':
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = self.data[namecount-1][currentsection][len(
                                        self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] + text_element
                                else:
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = self.data[namecount-1][currentsection][len(
                                        self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] + ' ' + text_element
                            else:
                                self.data[namecount-1][currentsection][len(
                                    self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = text_element

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
        self.logger.info("Reading and merging html files from {}".format(file_path))
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
                self.logger.info("Read {} in {} seconds".format(full_file_path, end_time))
        self.logger.info("Finished reading and merging html {} dir".format(processed_files))
        return main_html

    @cachetools.func.ttl_cache(maxsize=100000, ttl=1000 * 6000)
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

        start_time = time.time()
        soup = self.get_soup(html)
        print("Parsing html took {} seconds".format(time.time() - start_time))
        cleaned_up_soup = self.clean_up_soup(soup)
        main_div = cleaned_up_soup.find("div", {'id': "content"})
        if main_div is None:
            raise ValueError("Could not find main content div")
        table_headers = []
        category_entries = []
        for div in main_div.findChildren(recursive=False):
            div_text = str(div.get_text().encode("utf-8").strip())
            if re.match('[0-9]+[.][0-9]+[.]', div_text):
                # This is the mp name
                self.mp = ' '.join(div_text.replace(
                    "\xe2\x80\x93", "-").split(' ')[1:]).replace(
                        ',', '').replace(' -', ',')
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
                table = div
                if table is not None:
                    if in_table:
                        # table continuation over a page break found, process it
                        table_tr = table.find_all('tr')
                        for tr in list(table_tr):
                            section_content = {}
                            for n, inner_tr in list(enumerate(tr.find_all('th'))):
                                if not n > len(table_headers) - 1:
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

        pprint.pprint(self.data)

    def print_font_ids(self):
        pdfdata = open(self.input, 'r').read()
        xmldata = scraperwiki.pdftoxml(pdfdata).encode('utf8')
        root = lxml.etree.fromstring(xmldata)
        pages = list(root)

        # Font ids we need are specified on first page that have interests.
        page_index = 1

        for el in list(pages[page_index]):
            if el.tag == "fontspec":
                print(el.items())

    def write_html_to_file(self, html_str):
        with open("main_html_file.html", 'w') as outfile:
            outfile.write(html_str.encode('utf-8'))
            self.logger.info("Wrote html to %s" % self.output)

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

    # Not Applicapable to 2019 and 2020
    # scraper.scrape_pdf()

    # Read and parse the word doc
    # master_html = scraper.read_and_merge_html(file_path="docx_files")
    # write master_html to file
    # scraper.write_html_to_file(master_html)
    start_time = time.time()
    html = open("main.html", 'r').read()
    print("--- %s seconds ---" % (time.time() - start_time))
    scraper.parse_html_generated_from_doc(html)
    # scraper.write_results()
