from django.utils import unittest

from mock import patch, Mock

from pombola.core.recaptcha import recaptcha_client


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class RecaptchaTests(unittest.TestCase):
    @patch(
        "pombola.core.recaptcha.requests.get",
        return_value=MockResponse({"success": True}, 200),
    )
    def test_verify_success(self, requests_mock):
        result = recaptcha_client.verify("test-response")
        self.assertTrue(result)

    @patch(
        "pombola.core.recaptcha.requests.get",
        return_value=MockResponse({"success": False}, 200),
    )
    def test_verify_fail(self, requests_mock):
        result = recaptcha_client.verify("test-response")
        self.assertFalse(result)
