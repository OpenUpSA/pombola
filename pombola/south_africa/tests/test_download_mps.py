from django.test import TestCase
from nose.plugins.attrib import attr

@attr(country='south_africa')
class HomeViewTest(TestCase):
    def test_homepage_context(self):
        self.assertTrue(False)