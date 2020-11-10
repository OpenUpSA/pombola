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
import operator
import re
from datetime import datetime

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from pombola.core.models import Organisation, OrganisationKind, Person, Position

COMMITTEE_MATCHING_FILE = "pmg-attendance/pmg-pa-committee-matches.json"
COMMITTEE_MATCHING_FILE = "pmg-attendance/pmg-pa-committee-matches-134.json"
OUT_FILE = "pmg-attendance/pmg-pa-member-attendance.csv"
PMG_API_MEETINGS_BASE_URL = "https://api.pmg.org.za/committee-meeting/"


def write_to_csv(data, headings, name):
    print("Writing to %s" % name)
    with open(name, "w") as f:
        print("Headings: %s" % headings)
        writer = csv.DictWriter(f, fieldnames=headings)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def read_json_file(name):
    print("Reading %s" % name)
    with open(name, "r") as f:
        return json.loads(f.read())


def get_results_from_url(session, url):
    while True:
        response = session.get(url)
        data = response.json()
        for result in data["results"]:
            yield result
        if not data["next"]:
            break
        url = data["next"]


def get_next_pmg_meeting():
    session = requests.Session()
    response = session.get(PMG_API_MEETINGS_BASE_URL)

    url = PMG_API_MEETINGS_BASE_URL
    for result in get_results_from_url(session, url):
        yield result


def get_meeting_attendances(meeting):
    url = meeting["attendance_url"]
    session = requests.Session()
    for result in get_results_from_url(session, url):
        yield result


def get_pa_coms(com_matches, meeting):
    committee_id = meeting["committee"]["id"]
    print("Searching for PMG committee id %d" % committee_id)
    match = next(m for m in com_matches if m["pmg_id"] == str(committee_id))
    return [Organisation.objects.get(id=c['pa_id']) for c in match['pa_committees']]


def get_pa_person(attendance):
    # Example pa_link: "https://www.pa.org.za/person/lorraine-juliette-botha/"
    l = pa_link = attendance["member"]["pa_link"].rstrip("/")
    slug = l[l.rstrip("/").rindex("/") + 1 :]
    print("Searching for PA person with slug: %s" % slug)
    pa_person = Person.objects.get(slug=slug)
    return pa_person


def get_meeting_date(meeting):
    string_date = meeting["date"]
    string_date = string_date[: string_date.index("T")]
    return datetime.strptime(string_date, "%Y-%m-%d").date()


def get_was_member(pa_person, pa_com, meeting_date):
    return Position.objects.currently_active(meeting_date).filter(
        organisation=pa_com,
        person=pa_person
    ).exists()

def to_out_row(pmg_meeting, pmg_attendance, pa_committees, meeting_date, pa_person, was_member):
    """
    - pmg_member_id
    - pmg_member_name
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
    d = {
        "pmg_member_id": pmg_attendance['member_id'],
        "pmg_member_name": pmg_attendance['member']['name'],
        "pmg_meeting_link": pmg_meeting['url'],
        "meeting_date": pmg_meeting['date'],
        "pmg_committee_name": pmg_meeting['committee_id'],
        "pmg_committee_id": pmg_meeting['committee']['name'],
        # can be multiple
        "pa_committee_ids": ", ".join([str(c.id) for c in pa_committees]),
        # - pa_committee_name
        "alternate_member": pmg_attendance['alternate_member'],
        "pa_committee_member": was_member,
    }
    print("out_row:")
    print(json.dumps(d, indent=4))
    return d



class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        meetings = {}
        com_matches = read_json_file(COMMITTEE_MATCHING_FILE)
        out_data = []
        for meeting in get_next_pmg_meeting():
            # Check if seen before
            if meeting["id"] in meetings:
                continue
            # Mark as seen
            meetings[meeting["id"]] = True

            meeting_date = get_meeting_date(meeting)
            pa_coms = get_pa_coms(com_matches, meeting)
            for attendance in get_meeting_attendances(meeting):
                pa_person = get_pa_person(attendance)
                was_member = any(
                    get_was_member(pa_person, pa_com, meeting_date) for pa_com in pa_coms)
                out_data.append(to_out_row(
                    meeting, attendance, pa_coms, meeting_date, pa_person, was_member
                ))
            break

        headings = out_data[0].keys()
        write_to_csv(out_data, headings, OUT_FILE)
