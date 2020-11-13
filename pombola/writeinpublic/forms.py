from django import forms
from django.forms import SelectMultiple, ModelMultipleChoiceField, ModelChoiceField

from pombola.core.models import Person

from .client import WriteInPublic


class RecipientForm(forms.Form):
    # Dynamicly create fields so we can show either people or committees
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        choicefield = kwargs.pop('choicefield', ModelChoiceField(queryset=queryset))
        multiplechoicefield = kwargs.pop('multiplechoicefield', ModelMultipleChoiceField(queryset=queryset))
        multiple = kwargs.pop('multiple', True)
        super(RecipientForm, self).__init__(*args, **kwargs)
        if multiple:
            self.fields['persons'] = multiplechoicefield
        else:
            self.fields['persons'] = choicefield


class DraftForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.EmailField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)


from pombola.core.recaptcha import RecaptchaField

class PreviewForm(forms.Form):
    # g_recaptcha_response = RecaptchaField(required=True)

    def __init__(self, *args, **kwargs):
        super(PreviewForm, self).__init__(*args, **kwargs)
        self.fields["g-recaptcha-response"]= RecaptchaField(required=True)
    