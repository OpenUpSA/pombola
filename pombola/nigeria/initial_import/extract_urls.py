#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from bs4 import BeautifulSoup
import sys
import re

soup = BeautifulSoup( sys.stdin.read() )
# print soup.prettify()

title_re = re.compile('View My')

for link in soup.find_all('a'):
    if title_re.search(link.get_text()):
        print(link['href'])

