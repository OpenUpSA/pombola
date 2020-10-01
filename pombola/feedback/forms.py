from django import forms
from django.utils.translation import ugettext_lazy as _


class FeedbackForm(forms.Form):
    """
    Gather feedback
    """

    url = forms.URLField(
        widget   = forms.HiddenInput,
        required = False,
    )

    comment = forms.CharField(
        label  = _('Your feedback'),
        widget = forms.Textarea,
        max_length = 2000,
    )

    email = forms.EmailField(
        label  = _('Your email'),
        required = False,
        help_text = "optional - but lets us get back to you...",
    )
    
