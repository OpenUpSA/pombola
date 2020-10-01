from collections import OrderedDict
from formtools.wizard.views import NamedUrlSessionWizardView

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.urlresolvers import reverse

import logging

from pombola.core.models import Person, Organisation, Position

from .forms import RecipientForm, DraftForm, PreviewForm, ModelChoiceField
from .fields import CommiteeGroupedModelChoiceField
from .client import WriteInPublic
from .models import Configuration


logger = logging.getLogger(__name__)


class PersonAdapter(object):
    def filter(self, ids):
        return Person.objects.filter(id__in=ids)

    def get(self, object_id):
        return Person.objects.get(id=object_id)

    def get_by_id(self, object_id):
        return self.get(object_id)

    def get_form_kwargs(self, step=None):
        queryset = Person.objects.all().current_mps_with_email().order_by('legal_name')
        step_form_kwargs = {
            'recipients': {
                'queryset': queryset,
            },
        }
        return step_form_kwargs.get(step, {})

    def object_ids(self, objects):
        return [p.id for p in objects]

    def get_templates(self):
        return {
            'recipients': 'writeinpublic/person-write-recipients.html',
            'draft': 'writeinpublic/person-write-draft.html',
            'preview': 'writeinpublic/person-write-preview.html',
        }

    def get_form_initial(self, **kwargs):
        return {}


class CommitteeAdapter(object):
    def filter(self, ids):
        return Organisation.objects.filter(id__in=ids)

    def get(self, object_id):
        return Organisation.objects.get(pk=object_id)

    def get_by_id(self, object_id):
        return self.get(object_id)

    def get_form_kwargs(self, step=None):
        queryset = Organisation.objects.prefetch_related('contacts__kind')\
            .select_related('kind')\
            .contactable_committees().distinct()\
            .order_by_house_then_by('name')
        
        choicefield = CommiteeGroupedModelChoiceField(
            choices_groupby='kind.name',
            queryset=queryset,
            empty_label=None
        )
        step_form_kwargs = {
            'recipients': {
                'queryset': queryset,
                'choicefield': choicefield,
                'multiple': False,
            },
        }
        return step_form_kwargs.get(step, {})

    def object_ids(self, objects):
        return [objects.id]

    def get_templates(self):
        return {
            'recipients': 'writeinpublic/committee-write-recipients.html',
            'draft': 'writeinpublic/committee-write-draft.html',
            'preview': 'writeinpublic/committee-write-preview.html',
        }

    def get_form_initial(self, step, cleaned_data={}):
        recipients = cleaned_data.get('recipients')
        if recipients is None:
            return {}

        committee = recipients.get('persons')
        if committee is None:
            return {}

        return {
            'content': 'Dear {committee_name},\n\n'.format(committee_name=committee.name),
        }


class WriteInPublicMixin(object):
    def dispatch(self, *args, **kwargs):
        configuration_slug = kwargs['configuration_slug']
        configuration = Configuration.objects.get(slug=configuration_slug)

        self.app_name = kwargs.get('app_name')

        # FIXME: It would be nice if we didn't hardcode the configuration_slug
        # values here.
        self.adapter = {
            'south-africa-assembly': PersonAdapter,
            'south-africa-committees': CommitteeAdapter,
        }[configuration_slug]()

        self.client = WriteInPublic(
            configuration.url,
            configuration.username,
            configuration.api_key,
            configuration.instance_id,
            configuration.person_uuid_prefix,
            adapter=self.adapter
        )
        return super(WriteInPublicMixin, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        self.request.current_app = self.request.resolver_match.namespace
        return super(WriteInPublicMixin, self).render_to_response(context, **response_kwargs)

class PreventRevalidationMixin(object):
    """
    Mixin to prevent the revalidation of specific fields.

    From https://github.com/jazzband/django-formtools/issues/21.

    Added because the Captcha field can't be validated more than once.

    Add the mixin and an array of NO_REVALIDATION_FIELD_NAMES that you don't 
    want to be revalidated at the end of the wizard.
    """
    def process_step(self, form):
        for name in self.NO_REVALIDATION_FIELD_NAMES:
           if name in form.fields:
               self.storage.extra_data['skip_validation_%s' % name] = True
        return super(PreventRevalidationMixin, self).process_step(form)

    def get_form(self, step=None, *args, **kwargs):
        # From https://github.com/jazzband/django-formtools/issues/21
        form = super(PreventRevalidationMixin, self).get_form(step=step, *args, **kwargs)
        for name in self.NO_REVALIDATION_FIELD_NAMES:
           if name in form.fields and self.storage.extra_data.get('skip_validation_%s' % name):
                del form.fields[name]
        return form



FORMS = [
    ("recipients", RecipientForm),
    ("draft", DraftForm),
    ("preview", PreviewForm),
]


class WriteInPublicNewMessage(WriteInPublicMixin, PreventRevalidationMixin, NamedUrlSessionWizardView):
    NO_REVALIDATION_FIELD_NAMES = ['captcha']
    form_list = FORMS

    def get_form_kwargs(self, step=None):
        return self.adapter.get_form_kwargs(step=step)

    def get_form_initial(self, step):
        if step != 'recipients':
            recipients = self.get_cleaned_data_for_step('recipients')
            return self.adapter.get_form_initial(step=step, cleaned_data={'recipients': recipients})
        else:
            return super(WriteInPublicNewMessage, self).get_form_initial(step=step)

    def get(self, *args, **kwargs):
        step = kwargs.get('step')
        # If we have an ID in the URL and it matches someone, go straight to
        # /draft
        if 'person_id' in self.request.GET:
            person_id = self.request.GET['person_id']
            try:
                recipient = self.adapter.get_by_id(person_id)
                self.storage.set_step_data('recipients', {'recipients-persons': [recipient.id]})
                self.storage.current_step = 'draft'
                return redirect(self.get_step_url('draft'))
            except Person.DoesNotExist:
                pass

        # Check that the form contains valid data
        if step == 'draft' or step == 'preview':
            recipients = self.get_cleaned_data_for_step('recipients')
            if recipients is None or recipients.get('persons') == []:
                # Form is missing persons, restart process
                self.storage.reset()
                self.storage.current_step = self.steps.first
                return redirect(self.get_step_url(self.steps.first))

        return super(WriteInPublicNewMessage, self).get(*args, **kwargs)

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={'step': step}, current_app=self.request.resolver_match.namespace)

    def get_template_names(self):
        return [self.adapter.get_templates()[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        step = kwargs.get('step')
        context = super(WriteInPublicNewMessage, self).get_context_data(form=form, **kwargs)
        context['message'] = self.get_cleaned_data_for_step('draft')
        recipients = self.get_cleaned_data_for_step('recipients')

        if recipients is not None:
            persons = recipients.get('persons')
            if not isinstance(persons, Organisation) and step == 'draft':
                # On the draft step, check if all recipients are contactable
                # in WriteInPublic
                not_contactable = []
                contactable = []
                for person in persons:
                    try:
                        if not self.client.get_person_is_contactable(person):
                            not_contactable.append(person)
                        else:
                            contactable.append(person)
                    except Exception as e:
                        logger.error(e)
                        not_contactable.append(person)

                self.storage.set_step_data('recipients', {'recipients-persons': [p.id for p in contactable]})
                context['non_contactable'] = not_contactable
                context['persons'] = contactable
            else:
                context['persons'] = persons 
        return context

    def done(self, form_list, form_dict, **kwargs):
        persons = form_dict['recipients'].cleaned_data['persons']
        person_ids = self.adapter.object_ids(persons)
        message = form_dict['draft'].cleaned_data
        try:
            response = self.client.create_message(
                author_name=message['author_name'],
                author_email=message['author_email'],
                subject=message['subject'],
                content=message['content'],
                persons=person_ids,
            )
            if response.ok:
                message_id = response.json()['id']
                messages.success(self.request, 'Success, your message has been accepted.')
                return redirect(reverse('writeinpublic:writeinpublic-pending', current_app=self.request.resolver_match.namespace))
            else:
                messages.error(self.request, 'Sorry, there was an error sending your message, please try again. If this problem persists please contact us.')
                return redirect(reverse('writeinpublic:writeinpublic-new-message', current_app=self.request.resolver_match.namespace))
        except self.client.WriteInPublicException:
            messages.error(self.request, 'Sorry, there was an error connecting to the message service, please try again. If this problem persists please contact us.')
            return redirect(reverse('writeinpublic:writeinpublic-new-message', current_app=self.request.resolver_match.namespace))


class WriteInPublicMessage(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(WriteInPublicMessage, self).get_context_data(**kwargs)
        try:
            context['message'] = self.client.get_message(self.kwargs['message_id'])
        except self.client.WriteInPublicException:
            raise Http404("Couldn't find message with that ID")
        context['app_name'] = self.app_name
        return context


class WriteToRepresentativeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/messages.html'

    def dispatch(self, *args, **kwargs):
        return super(WriteToRepresentativeMessages, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WriteToRepresentativeMessages, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['person'] = person
        person_uri = 'https://www.pa.org.za/api/national-assembly/popolo.json#person-{}'.format(person.id)
        context['messages'] = self.client.get_messages(person_uri)
        return context

class WriteToCommitteeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/committee-messages.html'

    def get_context_data(self, **kwargs):
        context = super(WriteToCommitteeMessages, self).get_context_data(**kwargs)
        slug = self.kwargs['slug']
        committee = get_object_or_404(Organisation, slug=slug)
        context['committee'] = committee
        uri = self.client.person_uuid_prefix.format(committee.id)
        context['messages'] = self.client.get_messages(uri)
        return context
