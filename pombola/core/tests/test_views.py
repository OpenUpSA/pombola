from datetime import date

from BeautifulSoup import NavigableString
from contextlib import contextmanager
from django_date_extensions.fields import ApproximateDate
from django_webtest import WebTest
from django.contrib.auth.models import User
from django.test import TestCase

from slug_helpers.models import SlugRedirect

from pombola.core import models


class HomeViewTest(TestCase):

    def test_homepage_context(self):
        response = self.client.get('/')
        self.assertIn('featured_person', response.context)
        self.assertIn('featured_persons', response.context)


class PositionViewTest(WebTest):

    def setUp(self):
        self.person = models.Person.objects.create(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )

        self.person_hidden = models.Person.objects.create(
            legal_name = 'Test Hidden Person',
            slug       = 'test-hidden-person',
            hidden     = True
        )

        self.organisation_kind = models.OrganisationKind.objects.create(
            name = 'Foo',
            slug = 'foo',
        )
        self.organisation_kind.save()

        self.organisation = models.Organisation.objects.create(
            name = 'Test Org',
            slug = 'test-org',
            kind = self.organisation_kind,
        )
        self.national_assembly = models.Organisation.objects.create(
            name = 'National Assembly',
            slug = 'national-assembly',
            kind = self.organisation_kind,
        )

        self.org_slug_redirect = SlugRedirect.objects.create(
            old_object_slug='test-Blah-org',
            new_object=self.organisation,
        )

        self.title = models.PositionTitle.objects.create(
            name = 'Test title',
            slug = 'test-title',
        )
        self.title2 = models.PositionTitle.objects.create(
            name = 'Test position with place',
            slug = 'test-position-with-place',
        )
        self.member_title = models.PositionTitle.objects.create(
            name = 'Member',
            slug = 'member',
        )

        self.position = models.Position.objects.create(
            person = self.person,
            title  = self.title,
            organisation = self.organisation,
        )

        self.place_kind_constituency = models.PlaceKind.objects.create(
            name='Constituency',
            slug='constituency',
        )

        self.bobs_place = models.Place.objects.create(
            name="Bob's Place",
            slug='bobs_place',
            kind=self.place_kind_constituency,
        )

        self.place_slug_redirect = SlugRedirect.objects.create(
            old_object_slug='old_bobs_place',
            new_object=self.bobs_place,
        )

        self.position2 = models.Position.objects.create(
            person = self.person,
            title  = self.member_title,
            place = self.bobs_place,
            organisation = self.national_assembly,
        )

        self.kind_governmental = models.OrganisationKind.objects.create(
            name='Governmental',
        )
        self.parliament = models.Organisation.objects.create(
            kind=self.kind_governmental,
            name='National Assembly',
        )
        self.parliamentary_session_2013 = \
            models.ParliamentarySession.objects.create(
                start_date=date(2013, 3, 5),
                end_date=date(9999, 12, 31),
                slug='na2013',
                name='National Assembly 2013-',
                house=self.parliament,
            )
        self.parliamentary_session_2007 = \
            models.ParliamentarySession.objects.create(
                start_date=date(2007, 12, 28),
                end_date=date(2013, 1, 14),
                slug='na2007',
                name='National Assembly 2007-2013',
                house=self.parliament,
            )

    def test_position_page(self):
        # List of people with position title
        self.app.get('/position/nonexistent-position-title/', status=404)
        resp = self.app.get('/position/test-title/')
        resp.mustcontain('Test Person')
        resp = self.app.get('/position/test-title/?view=grid')
        # List of people with position title at orgs of a certain kind
        self.app.get('/position/test-title/nonexistent-org-kind/', status=404)
        resp = self.app.get('/position/test-title/foo/')
        resp.mustcontain('Test Person')
        # List of people with position title at particular org
        self.app.get('/position/test-title/foo/nonexistent-org/', status=404)
        resp = self.app.get('/position/test-title/foo/test-org/')
        resp.mustcontain('Test Person')

    def get_links_to_people(self, soup):
        def wanted_link(a):
            if not a.has_attr('href'):
                return False
            url = a['href']
            person_url = url.startswith('/person/')
            disqush_fragment = url.endswith('#disqus_thread')
            return person_url and not disqush_fragment
        return set(a['href'] for a in soup.findAll('a') if wanted_link(a))

    def test_position_page_hidden_person_not_linked(self):
        resp = self.app.get('/position/test-title/')
        resp.mustcontain('Test Person')
        self.assertNotIn('Test Hidden Person', resp.html)
        self.assertEqual(
            set(['/person/test-person/']),
            self.get_links_to_people(resp.html)
        )

    def test_position_on_person_page(self):
        resp = self.app.get('/person/test-person/experience/')
        resp.mustcontain('Test title', 'of <a href="/organisation/test-org/">Test Org</a>')

    def test_organisation_page(self):
        self.app.get('/organisation/missing-org/', status=404)
        with self.assertNumQueries(14):
            resp = self.app.get('/organisation/test-org/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/test-org/people/')
        resp.mustcontain('Test Person')
        resp = self.app.get('/organisation/is/foo/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/is/foo/?order=place')
        resp.mustcontain('Test Org')

    def test_organisation_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/')
        self.assertRedirects(resp, '/organisation/test-org/', status_code=302)

    def test_organisation_contact_details_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/contact_details/')
        self.assertRedirects(resp, '/organisation/test-org/contact_details/', status_code=302)

    def test_organisation_apperances_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/people/')
        self.assertRedirects(resp, '/organisation/test-org/people/', status_code=302)

    def test_place_page(self):
        self.app.get('/place/is/constituency/')
        self.app.get('/place/bobs_place/')

    def test_place_page_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/')
        self.assertRedirects(resp, '/place/bobs_place/', status_code=302)

    def test_place_page_people_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/people/')
        self.assertRedirects(resp, '/place/bobs_place/people/', status_code=302)

    def test_place_page_places_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/places/')
        self.assertRedirects(resp, '/place/bobs_place/places/', status_code=302)

    def test_place_page_hidden_person_not_linked(self):
        resp = self.app.get('/place/bobs_place/')
        resp.mustcontain('Test Person')
        self.assertNotIn('Test Hidden Person', resp.html)
        self.assertEqual(
            set([u'/person/test-person/']),
            self.get_links_to_people(resp.html)
        )

    def test_different_sessions(self):
        title = models.PositionTitle.objects.create(
            name='Member of the National Assembly',
            slug='member-national-assembly',
        )
        earlier_person = models.Person.objects.create(
            legal_name="John Much Earlier", slug='john-much-earlier'
        )
        models.Position.objects.create(
            person=earlier_person,
            organisation=self.parliament,
            start_date=ApproximateDate(year=2008, month=1, day=1),
            end_date=ApproximateDate(year=2012, month=12, day=31),
            title=title,
        )
        earlier_in_current_session = models.Person.objects.create(
            legal_name="Joe Earlier In Current Session",
            slug='joe-earlier-in-current-session'
        )
        models.Position.objects.create(
            person=earlier_in_current_session,
            organisation=self.parliament,
            start_date=ApproximateDate(year=2013, month=10, day=1),
            end_date=ApproximateDate(year=2015, month=7, day=20),
            title=title,
        )
        later_person = models.Person.objects.create(
            legal_name="Josephine Later", slug='josephine-later'
        )
        models.Position.objects.create(
            person=later_person,
            organisation=self.parliament,
            start_date=ApproximateDate(year=2013, month=10, day=1),
            end_date=ApproximateDate(future=True),
            title=title,
        )
        # Get the normal view - all current positions:
        resp = self.app.get('/position/member-national-assembly/')
        person_names = []
        for li in resp.html.find_all('li', class_='person-list-item'):
            span_name = li.find('span', class_='name')
            person_names.append(span_name.text)
        self.assertEqual(person_names, ['Josephine Later'])
        # Get all positions in the 2013 session:
        resp = self.app.get('/position/member-national-assembly/?session=na2013')
        person_names = []
        for li in resp.html.find_all('li', class_='person-list-item'):
            span_name = li.find('span', class_='name')
            person_names.append(span_name.text)
        person_names.sort()
        self.assertEqual(
            person_names,
            ['Joe Earlier In Current Session', 'Josephine Later']
        )
        # Get all positions in the 2013 session:
        resp = self.app.get('/position/member-national-assembly/?session=na2007')
        person_names = []
        for li in resp.html.find_all('li', class_='person-list-item'):
            span_name = li.find('span', class_='name')
            person_names.append(span_name.text)
        self.assertEqual(
            person_names,
            ['John Much Earlier'],
        )

    def test_shows_alphabetical_pagination_if_query_param_present(self):
        response = self.app.get('/position/test-title/foo/?a=1')
        self.assertEqual(
            len(response.html.findAll('ol', {'class': 'alphabet-links'})), 1)

    def test_shows_alphabetical_pagination_if_query_param_present_with_others(self):
        response = self.app.get(
            '/position/test-title/foo/?order=name&a=1')
        self.assertEqual(
            len(response.html.findAll('ol', {'class': 'alphabet-links'})), 1)

    def test_does_not_show_alphabetical_pagination_if_no_query_param(self):
        response = self.app.get('/position/test-title/foo/')
        self.assertEqual(
            len(response.html.findAll('ol', {'class': 'alphabet-links'})), 0)
        self.assertNotIn('alphabetical_link_from_query_parameter', response.context)

    def test_letters_link_to_the_right_url_if_query_param_present(self):
        response = self.app.get('/position/test-title/foo/?order=name&a=1')
        ol = response.html.find('ol', {'class': 'alphabet-links'})
        link = ol.find('a', text='P')['href']
        self.assertEqual(link, '?a=1&order=name&letter=P')
        self.assertTrue(response.context['alphabetical_link_from_query_parameter'])

