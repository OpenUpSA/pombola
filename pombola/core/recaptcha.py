from django.conf import settings
from functools import wraps
from django.core.exceptions import PermissionDenied
import requests
from django.conf import settings
from django.core.exceptions import ValidationError


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
                    raise PermissionDenied("Recaptcha invalid")
        return function(request, *args, **kwargs)

    return wrap

from django.forms.fields import Field, CharField

def validate_recaptcha(value):
    # Verify Recaptcha
    if settings.GOOGLE_RECAPTCHA_SECRET_KEY:
        # recaptcha_response = request.POST.get("g-recaptcha-response", "")
        if not recaptcha_client.verify(value):
            raise Exception("Recaptcha invalid")
            raise ValidationError("Recaptcha invalid")

class RecaptchaField(Field):
    def __init__(self, *args, **kwargs):
        super(RecaptchaField, self).__init__(*args, **kwargs)
        self.validators.append(validate_recaptcha)