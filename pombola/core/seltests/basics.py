from django.core.urlresolvers import reverse
from pombola.testing.selenium import PombolaSeleniumTestCase
from django.test.utils import override_settings
from nose.plugins.attrib import attr
from django_webtest import WebTest
from mock import patch


@attr(country="south_africa")
class CoreTestCase(WebTest):
    def test_home(self):
        response = self.app.get(reverse("home"))
        self.assertIn("Home", response)

    def test_static(self):
        """Test that the static files are being served"""
        response = self.app.get("/static/static_test.txt")
        self.assertTrue("static serving works!" in response)

    def test_404(self):
        """Test that proper 404 page is being shown"""
        response = self.app.get("/hash/bang/bosh", status=404)
        self.assertEqual(response.status_code, 404)
        self.assertTrue("Page Not Found" in response)

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY="test-key")
    @patch("pombola.search.recaptcha.recaptcha_client")
    def test_403(self, mocked_recaptcha_client):
        """Test that proper 404 page is being shown"""
        mocked_recaptcha_client.verify.return_value = False

        search_location_url = reverse("core_geocoder_search")
        response = self.app.get(
            "{0}?q={1}".format(search_location_url, "Cape Town"), status=403
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue("Request Forbidden" in response)

    def test_user_not_logged_in(self):
        """Test that by default user is not logged in"""
        response = self.app.get("/")

        self.assertTrue(response.context["user"].is_anonymous())
