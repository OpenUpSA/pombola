from django_webtest import WebTest
from django.utils.unittest import skip

from pombola.core import models

@skip("The South African site doesn't use this app")
class SmokeTests(WebTest):

    def testAllAppearances(self):

        person = models.Person(
            legal_name="Alfred Smith",
            slug='alfred-smith',
        )
        person.save()

        self.app.get('/hansard/person/alfred-smith/appearances/')
