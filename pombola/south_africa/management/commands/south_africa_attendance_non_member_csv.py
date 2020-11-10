"""
Out format:
 - pmg_member_id
 - member_name
 - pmg_meeting_link
 - meeting_date
 - pmg_committee_name
 - pmg_committee_id
 - pa_committee_id
 - pa_committee_name
 - alternate_member: taken from the alternate field in PMG
 - pa_committee_member: whether the person was a member of the committee at the 
     time according to the PA data
"""


import csv
import json
from datetime import datetime
import operator
import re

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from pombola.core.models import Organisation, OrganisationKind, Person

COMMITTEE_MATCHING_FILE = "pmg-attendance/pmg-pa-committee-matches.json"
COMMITTEE_MATCHING_FILE = "pmg-attendance/pmg-pa-committee-matches-134.json"
OUT_FILE = "pmg-attendance/pmg-pa-member-attendance.csv"
PMG_API_MEETINGS_BASE_URL = "https://api.pmg.org.za/committee-meeting/"

def write_to_csv(data, headings, name):
    print("Writing to %s" % name)
    with open(name, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=headings)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def read_json_file(name):
    print("Reading %s" % name)
    with open(name, 'r') as f:
        return json.loads(f.read())

def get_results_from_url(session, url):
    response = session.get(url)
    data = response.json()
    for result in data['results']:
        yield result

def get_next_pmg_meeting():
    session = requests.Session()
    response = session.get(PMG_API_MEETINGS_BASE_URL)

    url = PMG_API_MEETINGS_BASE_URL
    while True:
        for result in get_results_from_url(session, url):
            yield result
        if not data['next']:
            break
        url = data['next']
    
def get_meeting_attendances(meeting):
    url = meeting['attendance_url']
    session = requests.Session()
    while True:
        for result in get_results_from_url(session, url):
            yield result
        if not data['next']:
            break
        url = data['next']

def get_pa_com(com_matches, meeting):
    committee_id = meeting['committee']['id']
    print("Searching for PMG committee id %d" % committee_id)
    return next(m for m in com_matches if m['pmg_id'] == str(committee_id))

def get_pa_person(attendance):
    # Example pa_link: "https://www.pa.org.za/person/lorraine-juliette-botha/"
    l = pa_link = attendance['member']['pa_link'].rstrip('/')
    slug =l[l.rstrip('/').rindex('/')+1:]
    print("Searching for PA person with slug: %s" % slug)
    pa_person = Person.objects.get(slug=slug)
    return pa_person

def get_meeting_date(meeting):
    string_date = meeting['date']
    string_date = string_date[:string_date.index('T')]
    return datetime.strptime(string_date, "%Y-%m-%d").date()

def to_out_row(pmg_meeting, pa_meeting, attendance):
    pass

def get_was_member(pa_person, pa_com, meeting_date):
    return True
    pass

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        meetings = {}
        com_matches = read_json_file(COMMITTEE_MATCHING_FILE)
        out_data = []
        for meeting in get_next_pmg_meeting():
            # Check if seen before
            if meeting['id'] in meetings:
                continue
            # Mark as seen
            meetings[meeting['id']] = True

            meeting_date = get_meeting_date(meeting)
            pa_com = get_pa_com(com_matches, meeting)
            for attendance in get_meeting_attendances(meeting):
                pa_person = get_pa_person(attendance)
                pa_committee_member = get_was_member(pa_person, pa_com, meeting_date)

                break


            break

        headings = []
        write_to_csv(out_data, headings, OUT_FILE)