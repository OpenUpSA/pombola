import csv
import json
import operator
import re
from datetime import datetime, date
from django.core.management.base import BaseCommand

from .utils import *

ATTENDANCES_FILE = "pmg-attendance/pmg-pa-member-attendance.csv"
PEOPLE_NOT_FOUND_FILE = "pmg-attendance/pmg-members-not-found.csv"


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        attendances = read_csv_file(ATTENDANCES_FILE)
        people_not_found = read_csv_file(PEOPLE_NOT_FOUND_FILE)

        print("---- Attendances ----")
        num_attendances = attendances

        # Number of attendances
        print("Number of attendances: \t\t\t\t\t %d" % len(attendances))

        # Unique attendances
        uniq_attendances = uniqify_list(
            num_attendances, ["pmg_member_id", "pmg_meeting_link"]
        )
        print("Unique attendances: \t\t\t\t\t %d" % len(uniq_attendances))

        # Number non-member
        non_member_attendances = [
            a for a in uniq_attendances if a["pa_committee_member"] == "False"
        ]
        member_attendances = [
            a for a in uniq_attendances if a["pa_committee_member"] == "True"
        ]
        # print(
        #     "Non-member attendances: \t\t\t\t %d (%.2f%%)"
        #     % (
        #         len(non_member_attendances),
        #         perc(len(non_member_attendances), len(uniq_attendances)),
        #     )
        # )
        # print(
        #     "Member attendances: \t\t\t\t\t %d (%.2f%%)"
        #     % (
        #         len(member_attendances),
        #         perc(len(member_attendances), len(uniq_attendances)),
        #     )
        # )
        assert len(non_member_attendances) + len(member_attendances) == len(
            uniq_attendances
        )

        # Full-member attendance (not non-member and not-alternate)
        full_member_attendances = [
            a for a in member_attendances if a["alternate_member"] == "False"
        ]
        print(
            "Full-member attendances: \t\t\t\t %d (%.2f%%)"
            % (
                len(member_attendances),
                perc(len(member_attendances), len(uniq_attendances)),
            )
        )

        # Alternate member attendance
        alternate_attendances = [
            a for a in uniq_attendances if a["alternate_member"] == "True"
        ]
        print(
            "Alternate member attendances: \t\t\t\t %d (%.2f%%)"
            % (
                len(alternate_attendances),
                perc(len(alternate_attendances), len(uniq_attendances)),
            )
        )
        # Non-member and also not alternate member (the ones we really care about)
        non_member_and_non_alternate = [
            a
            for a in non_member_attendances
            if a["alternate_member"] == "False"
        ]
        print(
            "Non-member and non-alternate member attendances: \t %d (%.2f%%)"
            % (
                len(non_member_and_non_alternate),
                perc(len(non_member_and_non_alternate), len(uniq_attendances)),
            )
        )

        # Non-member and alternate member (shouldn't usually be possible)
        non_member_and_alternate = [
            a
            for a in non_member_attendances
            if a["alternate_member"] == "True"
        ]
        print(
            "Non-member and alternate member attendances: \t\t %d (%.2f%%)"
            % (
                len(non_member_and_alternate),
                perc(len(non_member_and_alternate), len(uniq_attendances)),
            )
        )
        assert len(non_member_and_non_alternate) + len(non_member_and_alternate) == len(
            non_member_attendances
        )


        print('\n')
        print("---- PMG people not found in PA ----")

        unique_people = set(a['pmg_member_id'] for a in uniq_attendances)
        print("Number PMG people with attendances: \t\t\t %d" % len(unique_people))

        # Number of people not found
        people_not_found_ids = set([p['pmg_member_id'] for p in people_not_found])
        print("Number of PMG people not found in PA: \t\t\t %d (%.2f%%)" % (
            len(people_not_found_ids),
            perc(len(people_not_found_ids), len(unique_people))
        )
        )

        print("PMG member IDs of people not found: \t\t\t %s" % ", ".join(people_not_found_ids))