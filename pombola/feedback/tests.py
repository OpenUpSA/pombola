"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from .models import Feedback


class CreateFeedbackTestCase(TestCase):
    def test_create_feedback_successfully(self):
        c = Client()
        self.assertEquals(0, Feedback.objects.count())
        response = c.post(
            "/feedback/",
            {
                "url": "http://example.com",
                "comment": "Hello",
            },
        )
        print(response)
        self.assertContains(response, "Thank you for your feedback!", status_code=200)
        self.assertEquals(1, Feedback.objects.count())

    def test_reject_without_recaptcha_token(self):
        c = Client()
        self.assertEquals(0, Feedback.objects.count())
        response = c.post(
            "/feedback/",
            {
                "url": "http://example.com",
                "comment": "Hello",
            },
        )
        print(response)
        self.assertContains(response, "Sorry, something went wrong", status_code=200)
        self.assertEquals(0, Feedback.objects.count())
