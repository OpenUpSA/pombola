from http import HTTPStatus
from django.test import TestCase


class FeedbackFormTest(TestCase):
    def test_success_post(self):
        """
        Tests that we submit the form successfully.
        """
        response = self.client.post(
            "/feedback/", 
            data={
                "comment": "change the page header to h1.",
                "email": "test@test.com",
                "url": "http://0.0.0.0:8000/person/qubudile-richard-dyantyi/",
                "g-recaptcha-response": "03AGdBq24_yN5E-tNGTrWp0gKsnyAFi_98_tENffZTIPAjUPo6Be1SQF8OUFkRNnhoVkaJVbaoU30_gt1FVEumjIFNaU3hcrijVw8qu7P8gNOfPVpqsXWcGt5oV70adSyzDr9MsxNTrIgOgyhcSIdW2SZ0tEGxAST02WbVljE90SfGhpD8DZkWKzODmiNpGXWWB2B6dV-10eBDqGsBwYXnNwgDhvHx6I-N9p5jfT7ZxvWBd9RetLPw94tJGjkxTYbet-s0emVGqxKneSarmaTrr9qwrlIPMfP2oUoBqxuUqKbMmfzdKyermSgPbGMvks48DU9WIDXkzDqWdKw_cX3PColKVwepqY9LS7IdWTEB9rsDxiFUzeXE7xKRvcGBne5IezW4RzfHekftVVuN9o9a7KJdOQZYOBPSEAzDL81QxyZl3db9fjxsYullZ4hEZvJnY-N_WlgEG8uj"
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, "<div class='success'>Thank you for your feedback!</div>", html=True
        )
