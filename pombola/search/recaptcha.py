from django.conf import settings
from django.http import HttpResponse
from functools import wraps
import requests


class ReCaptchaClient(object):
    """
    Client to verify Google ReCAPTCHA responses. 
    """

    endpoint = "https://www.google.com/recaptcha/api/siteverify"

    def __init__(self, secret):
        self.secret = secret

    def verify(self, response):
        """
        Verify a Google reCAPTCHA 2.0 response.
        """

        params = {}
        params["secret"] = self.secret
        params["response"] = response

        response = requests.get(self.endpoint, params=params)
        result = response.json()

        return result.get("success", False)


recaptcha_client = ReCaptchaClient(settings.GOOGLE_RECAPTCHA_SECRET_KEY)


def check_recaptcha_is_valid_if_query_param_present(function, query_param):
    """
    Checks that the ReCAPTCHA response is valid if a given query parameter
    is present in the request.

    If the query parameter isn't present, return the function as normally.
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.GET.get(query_param, False):
            if settings.GOOGLE_RECAPTCHA_SECRET_KEY:
                recaptcha_response = request.GET.get("g-recaptcha-response", "")
                if not recaptcha_client.verify(recaptcha_response):
                    return HttpResponse(status=403)
        return function(request, *args, **kwargs)

    return wrap
