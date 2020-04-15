from django.conf import settings
from django.http import HttpResponse
from functools import wraps
import requests


class ReCaptchaClient(object):
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


def recaptcha_is_valid(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if settings.GOOGLE_RECAPTCHA_SECRET_KEY:
            recaptcha_response = request.GET.get("g-recaptcha-response", "")
            if not recaptcha_client.verify(recaptcha_response):
                return HttpResponse(status=403)
        return function(request, *args, **kwargs)

    return wrap


class ReCaptchaMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(ReCaptchaMixin, cls).as_view(**initkwargs)
        return recaptcha_is_valid(view)
