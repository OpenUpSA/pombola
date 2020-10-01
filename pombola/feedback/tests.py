from django.test import TestCase
from mock import patch
from django.test.utils import override_settings
from models import Feedback

class FeedbackFormTest(TestCase):

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY='test-key')
    @patch('pombola.feedback.views.recaptcha_client')
    def test_success_post_with_recaptcha(self, mocked_recaptcha_client):
        """
        Tests that we submit the form successfully.
        """
        mocked_recaptcha_client.verify.return_value = True
        response = self.client.post(
            "/feedback/", 
            data={
                "comment": "change the page header to h1.",
                "email": "test@test.com",
                "url": "http://0.0.0.0:8000/person/qubudile-richard-dyantyi/",
                "g-recaptcha-response": "test"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "<div class='success'>Thank you for your feedback!</div>", html=True
        )
        self.assertEquals(1, Feedback.objects.count())

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY='test-key')
    @patch('pombola.feedback.views.recaptcha_client')
    def test_fail_post_with_recaptcha(self, mocked_recaptcha_client):
        """
        Tests that the submit feedback fails.
        """
        mocked_recaptcha_client.verify.return_value = False
        response = self.client.post(
            "/feedback/", 
            data={
                "comment": "change the page header to h1.",
                "email": "test@test.com",
                "url": "http://0.0.0.0:8000/person/qubudile-richard-dyantyi/",
                "g-recaptcha-response": "test"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Sorry, something went wrong. Please try again or email us at <a href='mailto:contact@pa.org.za'>contact@pa.org.za</a>"
        )
        self.assertEquals(0, Feedback.objects.count())