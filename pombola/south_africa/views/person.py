from __future__ import division

import dateutil
import json
import logging
import re
import requests
import urllib
import datetime
import pytz

from .constants import API_REQUESTS_TIMEOUT
from urlparse import urlsplit

from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.db.models import Q

from pombola.core import models
from pombola.core.views import PersonDetail, PersonSpeakerMappingsMixin
from pombola.interests_register.models import Release

from speeches.models import Speech

logger = logging.getLogger('django.request')


class AttendanceAPIDown(Exception):
    pass


class SAPersonDetail(PersonSpeakerMappingsMixin, PersonDetail):
    important_org_kind_slugs = (
        'national-executive', 'parliament', 'provincial-legislature')

    # Meanings of attendance field
    #  A:   Absent
    #  AP:  Absent with Apologies
    #  DE:  Departed Early
    #  L:   Arrived Late
    #  LDE: Arrived Late and Departed Early
    #  P:   Present
    present_values = set(('P', 'DE', 'L', 'LDE'))

    def get_recent_speeches_for_section(self, tags, limit=5):
        pombola_person = self.object
        sayit_speaker = self.pombola_person_to_sayit_speaker(pombola_person)

        if not sayit_speaker:
            # Without a speaker we can't find any speeches
            return Speech.objects.none()

        speeches = Speech.objects \
            .filter(tags__name__in=tags, speaker=sayit_speaker) \
            .order_by('-start_date', '-start_time')

        if limit:
            speeches = speeches[:limit]

        return speeches

    def get_tabulated_interests(self):
        interests = self.object.interests_register_entries.all()
        tabulated = {}

        release_content_type = ContentType.objects.get_for_model(Release)

        for entry in interests:
            release = entry.release
            release_name = release.name
            release_year = release_name[-4:]
            category = entry.category

            if release.id not in tabulated:
                sources = models.InformationSource.objects.filter(
                    content_type=release_content_type,
                    object_id=release.id
                )
                tabulated[release.id] = {
                    'name': release_name,
                    'categories': {},
                    'informationsource': sources,
                    'release_year': release_name[-4:]
                }

            if category.id not in tabulated[release.id]['categories']:
                tabulated[release.id]['categories'][category.id] = {
                    'name': category.name,
                    'headings': [],
                    'headingindex': {},
                    'headingcount': 1,
                    'entries': [],
                    'category_id': "{}_{}".format(
                        release_name, category.name
                    ),
                }

            #create row list
            tabulated[release.id]['categories'][category.id]['entries'].append(
                [''] * (tabulated[entry.release.id]['categories'][entry.category.id]['headingcount'] - 1)
            )

            #loop through each 'cell' in the row
            for entrylistitem in entry.line_items.all():
                #if the heading for the column does not yet exist, create it
                if entrylistitem.key not in tabulated[entry.release.id]['categories'][entry.category.id]['headingindex']:
                    tabulated[release.id]['categories'][category.id]['headingindex'][entrylistitem.key] = tabulated[entry.release.id]['categories'][entry.category.id]['headingcount'] - 1
                    tabulated[release.id]['categories'][category.id]['headingcount'] += 1
                    tabulated[release.id]['categories'][category.id]['headings'].append(entrylistitem.key)

                    #loop through each row that already exists to ensure lists are the same size
                    for (key, line) in enumerate(tabulated[release.id]['categories'][category.id]['entries']):
                        tabulated[entry.release.id]['categories'][entry.category.id]['entries'][key].append('')

                #record the 'cell' in the correct position in the row list
                tabulated[release.id]['categories'][category.id]['entries'][-1][tabulated[release.id]['categories'][category.id]['headingindex'][entrylistitem.key]] = entrylistitem.value

        tabulated_interests = []

        for release_id, release_data in tabulated.items():
            release = Release.objects.get(pk=release_id)

            tabulated_interests.append((release_data, release.date))

        tabulated_interests.sort(key=lambda x: x[1], reverse=True)

        return tabulated_interests

    def list_contacts_by_kind(self, kind_slugs):
        return self.object.contacts \
            .filter(kind__slug__in=kind_slugs)

    def list_contacts_values(self, kind_slugs):
        return self.list_contacts_by_kind(kind_slugs) \
            .values_list('value', flat=True)

    def list_contacts_with_preferred(self, kind_slugs):
        return self.list_contacts_by_kind(kind_slugs) \
            .values_list('value', 'preferred')

    def get_former_parties(self, person):
        former_party_memberships = (
            person
            .position_set
            .all()
            .filter(
                # select the political party memberships
                (Q(title__slug='member') & Q(organisation__kind__slug='party'))
            )
            .order_by('-start_date')
        )
        return models.Organisation.objects.filter(
            position__in=former_party_memberships).distinct()

    def store_or_get_pmg_member_id(self, scheme='za.org.pmg.api/member'):
        try:
            identifier = self.object.get_identifiers(scheme)[0]
        except:
            identifier = None

        if not identifier:
            # First find the id of the person
            pa_link = urllib.quote(
                "https://www.pa.org.za/person/{}/".format(self.object.slug))

            url_fmt = "https://api.pmg.org.za/member/?filter[pa_link]={}"
            api_search_url = url_fmt.format(pa_link)
            try:
                search_resp = requests.get(
                    api_search_url, timeout=API_REQUESTS_TIMEOUT)
            except requests.exceptions.RequestException:
                raise AttendanceAPIDown
            search_data = json.loads(search_resp.text)

            if not search_data.get('count'):
                return None

            if search_data['count'] > 1:
                logger.error(
                    'Duplicate members at PMG with slug {} - SKIPPING'.format(self.object.slug))
                return None

            identifier = search_data['results'][0]['id']

            models.Identifier.objects.create(
                scheme=scheme,
                identifier=identifier,
                content_object=self.object,
            )

        return identifier

    def get_active_minister_positions(self, years):
        """
        Return a year:active_ministerial_position dict for the list of years provided
        """
        active_minister_positions = {}

        for year in years:
            active_minister_positions[year] = self.object.position_set \
                .title_slug_prefixes(['minister', 'deputy-minister']) \
                .active_during_year(year)

        return active_minister_positions

    def active_position_at_date(self, positions, date):
        """
        Check whether one of the positions were active on the date
        """
        for position in positions:
            if position.is_active_at_date(date.strftime("%Y-%m-%d")):
                return True
        return False

    def get_attendance_data_url(self, attendance_url_template="https://api.pmg.org.za/member/{}/attendance/"):
        identifier = self.store_or_get_pmg_member_id()

        if identifier:
            return attendance_url_template.format(identifier)

    def download_attendance_data(self):
        attendance_url = next_url = self.get_attendance_data_url()

        cache = caches['pmg_api']
        results = cache.get(attendance_url)

        if results is None:
            results = []
            while next_url:
                try:
                    resp = requests.get(next_url, timeout=API_REQUESTS_TIMEOUT)
                except requests.exceptions.RequestException:
                    raise AttendanceAPIDown

                data = json.loads(resp.text)
                results.extend(data.get('results'))

                next_url = data.get('next')

            cache.set(attendance_url, results)

        # Results are returned from the API most recent first, which
        # is convenient for us.
        return results

    def get_attendance_stats_raw(self, data):
        if not data:
            return {}

        attendance_by_year = {}
        split_date = datetime.datetime(2024, 6, 1, tzinfo=pytz.utc)  # Ensure split_date is timezone-aware

        years = sorted(set(dateutil.parser.parse(x['meeting']['date']).year for x in data), reverse=True)
        minister_positions_by_year = self.get_active_minister_positions(years)

        for x in data:
            if x['alternate_member']:
                # Don't count alternate member attendances
                continue
            attendance = x['attendance']
            meeting_date = dateutil.parser.parse(x['meeting']['date']).astimezone(pytz.utc)  # Ensure meeting_date is timezone-aware
            year = meeting_date.year

            if year == 2024:
                split_key = 'before' if meeting_date < split_date else 'after'
                split_year = "{}_{}".format(year, split_key)
            else:
                split_year = str(year)

            base_year = year if year != 2024 else 2024  # Use 2024 as the base year for splitting
            minister_at_date = self.active_position_at_date(minister_positions_by_year[base_year], meeting_date)
            position = 'minister' if minister_at_date else 'mp'

            year_dict = attendance_by_year.setdefault(split_year, {})
            position_dict = year_dict.setdefault(position, {})
            position_dict.setdefault(attendance, 0)
            position_dict[attendance] += 1

        # Add zero minister attendance if person was active minister during a year,
        # but no records were returned for that year.
        for year, positions in minister_positions_by_year.items():
            if positions:
                # There were active minister positions
                if year == 2024:
                    for split_key in ['before', 'after']:
                        split_year = "{}_{}".format(year, split_key)
                        if 'minister' not in attendance_by_year.get(split_year, {}).keys():
                            # No minister attendance recorded
                            attendance_by_year.setdefault(split_year, {})['minister'] = {'P': 0}
                elif 'minister' not in attendance_by_year.get(str(year), {}).keys():
                    # No minister attendance recorded
                    attendance_by_year[str(year)]['minister'] = {'P': 0}

        return attendance_by_year
    
    def get_meetings_attended(self, data, limit=None):
        api_url_re = r'/committee-meeting/(\d+)/'
        meeting_url_template = 'https://pmg.org.za/committee-meeting/{}/'

        if limit:
            meetings = [x['meeting'] for x in data if x['attendance'] in self.present_values][:limit]
        else:
            meetings = [x['meeting'] for x in data if x['attendance'] in self.present_values]

        results = []
        for meeting in meetings:
            api_url = meeting['url']
            path = urlsplit(api_url).path
            meeting_id = re.match(api_url_re, path).group(1)

            meeting_summary = {
                'url': meeting_url_template.format(meeting_id),
                'title': meeting['title'],
                'committee_name': meeting['committee']['name'],
                'date': dateutil.parser.parse(meeting['date']).date()
            }

            if not limit:
                meeting_summary['summary'] = meeting.get('summary', None)

            results.append(meeting_summary)


        return results

    def get_position_for_year(self, year):
        # Check if the Person held an active ministerial position the last day
        # of the year. Return 'minister' if so, 'mp' if not.

        active_minister = self.object.position_set \
            .title_slug_prefixes(['minister', 'deputy-minister']) \
            .active_at_end_of_year(year) \
            .select_related('person')

        if active_minister:
            return 'minister'
        else:
            return 'mp'
    
    def get_attendance_stats(self, attendance_by_year):
        sorted_keys = sorted(attendance_by_year.keys(), reverse=True)
        return_data = []

        for year in sorted_keys:
            year_dict = attendance_by_year[year]

            for position in sorted(year_dict.keys()):
                attendance = sum((year_dict[position][x] for x in year_dict[position] if x in self.present_values))
                meeting_count = sum((year_dict[position][x] for x in year_dict[position]))
                if meeting_count == 0:
                    percentage = 0
                else:
                    percentage = 100 * attendance / meeting_count

                year_label = year.replace('_before', ' (6th Parliament)').replace('_after', ' (7th Parliament)')
                
                return_data.append(
                    {
                        'year': year_label,
                        'attended': attendance,
                        'total': meeting_count,
                        'percentage': percentage,
                        'position': position if position == 'mp' else 'minister/deputy',
                    }
                )

        # 2024 is split for 6th and 7th parliament. This puts 7th parliament before 6th in the list.
        if 1 < len(return_data) and return_data[0]['year'] == '2024 (6th Parliament)':
            return_data.insert(1, return_data.pop(0))

        return return_data

    def get_attendance_data_for_display(self):
        raw_data = self.download_attendance_data()
        attendance_by_year = self.get_attendance_stats_raw(raw_data)
        attendance_stats = self.get_attendance_stats(attendance_by_year)
        latest_meetings_attended = self.get_meetings_attended(raw_data, limit=5)

        return attendance_stats, latest_meetings_attended

    def get_context_data(self, **kwargs):
        context = super(SAPersonDetail, self).get_context_data(**kwargs)
        context['twitter_contacts'] = self.list_contacts_values(('twitter',))
        context['facebook_contacts'] = self.list_contacts_values(('facebook',))
        context['linkedin_contacts'] = self.list_contacts_values(('linkedin',))
        context['youtube_contacts'] = self.list_contacts_values(('youtube',))
        context['whoswhosa_contacts'] = self.list_contacts_values(('whos-who-sa',))
        context['instagram_contacts'] = self.list_contacts_values(('instagram',))
        # The email attribute of the person might also be duplicated
        # in a contact of type email, so create a set of email
        # addresses:
        email_contacts = set(self.list_contacts_with_preferred(('email',)))
        if self.object.email:
            email_contacts.add((self.object.email, True))

        context['email_contacts'] = sorted(email_contacts, key=lambda tup: not tup[1])
        context['phone_contacts'] = self.list_contacts_values(('cell', 'voice'))
        context['fax_contacts'] = self.list_contacts_values(('fax',))
        context['address_contacts'] = self.list_contacts_values(('address',))

        orgs_from_important_positions = models.Organisation.objects.filter(
            kind__slug__in=self.important_org_kind_slugs,
            position__in=self.object.politician_positions(),
        )

        former_important_positions = (
            self.object.position_set
            .all()
            .political()
            .previous()
            .filter(organisation__kind__slug__in=self.important_org_kind_slugs)
        )

        former_orgs_from_important_positions = models.Organisation.objects.filter(
            position__in=former_important_positions,
        ).exclude(id__in=orgs_from_important_positions)

        context['organizations_from_important_positions'] = \
            orgs_from_important_positions.distinct()

        context['organizations_from_former_important_positions'] = \
            former_orgs_from_important_positions.distinct()

        # FIXME - the titles used here will need to be checked and fixed.
        context['hansard'] = self.get_recent_speeches_for_section(
            ('hansard',), limit=2)
        context['committee'] = self.get_recent_speeches_for_section(
            ('committee',), limit=5)
        context['question'] = self.get_recent_speeches_for_section(
            ('question', 'answer'), limit=3)

        context['interests'] = self.get_tabulated_interests()
        if self.object.date_of_death is not None:
            context['former_parties'] = self.get_former_parties(self.object)

        show_attendance = False
        for party in self.object.parties():
            if party.show_attendance:
                show_attendance = True
        if show_attendance:
            try:
                context['attendance'], context['latest_meetings_attended'] = \
                    self.get_attendance_data_for_display()
            except AttendanceAPIDown:
                context['attendance'] = context['latest_meetings_attended'] = \
                    'UNAVAILABLE'

        return context
