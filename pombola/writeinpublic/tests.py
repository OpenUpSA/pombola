from datetime import datetime

import requests_mock
from mock import Mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from django.forms import ModelMultipleChoiceField, ModelChoiceField
from django.test.utils import override_settings
from mock import patch

from pombola.core.models import Person, Organisation, OrganisationKind, ContactKind

from . import client
from .models import Configuration
from .views import PersonAdapter, CommitteeAdapter
from .forms import RecipientForm

person_json = {
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [
        {
            "additional_name": "",
            "biography": "",
            "birth_date": "",
            "created_at": "2020-06-04T04:54:11.320858",
            "death_date": "",
            "email": "aseabi@parliament.gov.za",
            "end_date": None,
            "family_name": "",
            "gender": "",
            "given_name": "",
            "honorific_prefix": "",
            "honorific_suffix": "",
            "id": 319,
            "identifiers": [
                {
                    "id": 640,
                    "identifier": "9684",
                    "object_id": 319,
                    "resource_uri": "",
                    "scheme": "popolo:person"
                },
                {
                    "id": 641,
                    "identifier": "https://pa.org.za/api/national-assembly/popolo.json#person-9684",
                    "object_id": 319,
                    "resource_uri": "",
                    "scheme": "popolo_uri"
                }
            ],
            "image": None,
            "name": "Albert Mammoga Seabi",
            "national_identity": None,
            "patronymic_name": "",
            "popit_id": None,
            "popit_url": "https://pa.org.za/api/national-assembly/popolo.json#person-9684",
            "resource_uri": "https://pa.org.za/api/national-assembly/popolo.json#person-9684",
            "sort_name": "",
            "start_date": None,
            "summary": "",
            "updated_at": "2020-06-09T08:43:45.466050"
        }
    ]
}


@requests_mock.Mocker()
class ClientTest(TestCase):
    def setUp(self):
        self.adapter_mock = Mock()
        self.writeinpublic = client.WriteInPublic(
            'https://example.com',
            'test',
            '123',
            '42',
            'https://example.net/p.json#person-{}',
            adapter=self.adapter_mock
        )

    def test_create_message(self, m):
        m.post('/api/v1/message/')
        self.writeinpublic.create_message(
            author_name='Alice',
            author_email='alice@example.org',
            subject='Test subject',
            content='Hello, testing.',
            persons=['1'],
        )
        expected_json = {
            'writeitinstance': '/api/v1/instance/42/',
            'author_email': 'alice@example.org',
            'author_name': 'Alice',
            'content': 'Hello, testing.',
            'persons': ['https://example.net/p.json#person-1'],
            'subject': 'Test subject',
        }
        expected_url = 'https://example.com/api/v1/message/?username=test&api_key=123&format=json'
        last_request = m._adapter.last_request
        self.assertEqual(last_request.json(), expected_json)
        self.assertEqual(last_request.url, expected_url)

    def test_get_message(self, m):
        message_json = {
            'id': '1',
            'author_name': 'Alice',
            'subject': 'Test message',
            'content': 'Test content',
            'created': '2017-11-14T04:01:05.799658',
            'persons': [
                'http://example.com/popolo.json#person-123',
            ],
            'answers': [
                {
                    'content': 'Test',
                    'created': '2017-12-01T10:27:30.825490',
                    'person': {
                        'resource_uri': 'http://example.com/popolo.json#person-456',
                    },
                },
            ],
        }
        m.get('/api/v1/message/1/', json=message_json)
        message = self.writeinpublic.get_message(1)
        self.assertEqual(message.id, '1')
        self.assertEqual(message.author_name, 'Alice')
        self.assertEqual(message.subject, 'Test message')
        self.assertEqual(message.content, 'Test content')
        self.assertEqual(message.created_at, parse_datetime(message_json['created']))

        message.people()
        self.adapter_mock.filter.assert_called_once_with(ids=['123'])

        answers = message.answers()
        self.adapter_mock.get.assert_called_once_with('456')
        answer = answers[0]
        self.assertEqual('Test', answer.content)
        self.assertEqual(datetime(2017, 12, 1, 10, 27, 30, 825490), answer.created_at)


    def test_get_messages(self, m):
        messages_json = {
            'objects': [
                {
                    'id': '1',
                    'author_name': 'Alice',
                    'subject': 'Test message',
                    'content': 'Test content',
                    'created': '2017-11-14T04:01:05.799658',
                },
                {
                    'id': '2',
                    'author_name': 'Bob',
                    'subject': 'Another test message',
                    'content': 'More test content',
                    'created': '2017-11-15T05:05:04.345258',
                },
            ],
        }
        m.get('/api/v1/instance/42/messages/', json=messages_json)
        popolo_uri = 'https://example.net/p.json#person-1'
        messages = self.writeinpublic.get_messages(popolo_uri)
        last_request = m._adapter.last_request
        expected_qs = {
            'username': ['test'],
            'api_key': ['123'],
            'format': ['json'],
            'person__popolo_uri': [popolo_uri],
        }
        self.assertEqual(last_request.qs, expected_qs)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subject, 'Test message')
        self.assertEqual(messages[1].subject, 'Another test message')

    def test_get_person(self, m):
        m.get('/api/v1/person/', json=person_json)
        person = Person.objects.create(
            legal_name="Jimmy Stewart",
            slug="jimmy-stewart")
        person_result = self.writeinpublic.get_person(person)
        last_request = m._adapter.last_request
        expected_qs = {
            'username': ['test'],
            'api_key': ['123'],
            'format': ['json'],
            'identifiers__scheme': ['popolo:person'],
            'identifiers__identifier': [str(person.id)],
        }
        self.assertEqual(last_request.qs, expected_qs)
        self.assertEqual(len(person_result), 1)
        self.assertEqual(person_result[0]['email'], person_json['objects'][0]['email'])

    def test_get_person_is_contactable(self, m):
        m.get('/api/v1/person/', json=person_json)
        person = Person.objects.create(
            name="Jimmy Stewart",
            slug="jimmy-stewart")
        result = self.writeinpublic.get_person_is_contactable(person)
        last_request = m._adapter.last_request
        expected_qs = {
            'username': ['test'],
            'api_key': ['123'],
            'format': ['json'],
            'identifiers__scheme': ['popolo:person'],
            'identifiers__identifier': [str(person.id)],
            'has_contacts': ['true'],
            'instance_id': ['42']
        }
        self.assertEqual(last_request.qs, expected_qs)
        self.assertTrue(result)


@requests_mock.Mocker()
class WriteInPublicNewMessageViewTest(TestCase):
    def _setup_recatpcha_test(self, requests_mock):
        # Mock the POST response
        requests_mock.post('/api/v1/message/', json={
            'id': '42'
        })
        requests_mock.get('/api/v1/person/', json=person_json)
        configuration = Configuration.objects.create(
            url='http://example.com',
            username='admin',
            api_key='test',
            instance_id='1',
            slug='south-africa-assembly'
        )
        person = Person.objects.create()
        parliament = OrganisationKind.objects.create(slug='parliament', name='Parliament')
        na = Organisation.objects.create(slug='national-assembly', name='National Assembly', kind=parliament)
        person.position_set.create(organisation=na)
        ck_email, _ = ContactKind.objects.get_or_create(slug='email', name='Email')
        person.contacts.create(kind=ck_email, value='test@example.com', preferred=True)
        return person

    def _test_recaptcha_recipients_to_draft_steps(self, person):
        response = self.client.get(reverse('writeinpublic:writeinpublic-new-message'))
        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'recipients'}))

        # GET the recipients step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the recipients step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'recipients'}), {
            'write_in_public_new_message-current_step': 'recipients',
            'recipients-persons': person.id,
        })

        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'draft'}))

        # GET the draft step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the draft step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'draft'}), {
            'write_in_public_new_message-current_step': 'draft',
            'draft-subject': 'Test',
            'draft-content': 'Test',
            'draft-author_name': 'Test',
            'draft-author_email': 'test@example.com',
        })
        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'preview'}))

        return response

    def _test_successful_sending_wizard_steps(self, requests_mock):
        person = self._setup_recatpcha_test(requests_mock)

        response = self._test_recaptcha_recipients_to_draft_steps(person)

        # GET the preview step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the preview step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'preview'}), {
            'write_in_public_new_message-current_step': 'preview',
        })
        self.assertRedirects(
            response,
            reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'done'}),
            fetch_redirect_response=False
        )

        # GET the done step
        response = self.client.get(response.url)

        # Check that we're redirected to the pending message page
        self.assertRedirects(
            response,
            reverse('writeinpublic:writeinpublic-pending'),
            fetch_redirect_response=False
        )

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY=None)
    @patch('pombola.writeinpublic.views.recaptcha_client')
    def test_sending_message_wizard_steps_works_with_successful_recaptcha(self, requests_mock, mocked_recaptcha_client):
        mocked_recaptcha_client.verify.return_value = True

        self._test_successful_sending_wizard_steps(requests_mock)

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY=None)
    def test_sending_message_wizard_steps_works_without_recaptcha(self, requests_mock):
        self._test_successful_sending_wizard_steps(requests_mock)

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY='test-key')
    @patch('pombola.writeinpublic.views.recaptcha_client')
    def test_sending_message_wizard_steps_raises_error_with_incorrect_recaptcha(self, requests_mock, mocked_recaptcha_client):
        mocked_recaptcha_client.verify.return_value = False

        person = self._setup_recatpcha_test(requests_mock)

        response = self._test_recaptcha_recipients_to_draft_steps(person)

        # GET the preview step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the preview step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', 
            kwargs={'step': 'preview'}), {
                'write_in_public_new_message-current_step': 'preview',
            }, follow=True
        )

        # After unsuccessful Recaptcha, return to the preview page
        self.assertRedirects(
            response,
            reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'preview'}),
            fetch_redirect_response=False
        )
        
        # Check that the error message is in the context
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, "error")
        expected_message = 'Sorry, there was an error sending your message, please try again. If this problem persists please contact us.'
        self.assertTrue(expected_message in message.message)




@requests_mock.Mocker()
class WriteToCommitteeMessagesViewTest(TestCase):
    def setUp(self):
        Configuration.objects.create(
            url='http://example.com',
            username='admin',
            api_key='test',
            instance_id='1',
            slug='south-africa-committees',
            person_uuid_prefix='http://example.org/popolo.json#person-{}'
        )
        na_kind = OrganisationKind.objects.create(
            name='National Assembly', slug='national-assembly-committees')
        ncop_kind = OrganisationKind.objects.create(
            name='NCOP', slug='ncop-committees')
        self.na_committee = Organisation.objects.create(
            slug='test-na-committee', name='NA Test Committee', kind=na_kind)
        self.ncop_committee = Organisation.objects.create(
            slug='test-ncop-committee', name='NCOP Test Committee', kind=ncop_kind)
        email_kind, _ = ContactKind.objects.get_or_create(slug='email', name='Email')
        self.na_committee.contacts.create(
            kind=email_kind, 
            value='test@example.com', preferred=True)
        self.ncop_committee.contacts.create(
            kind=email_kind, 
            value='test@example.com', preferred=True)

    def test_committees_that_exists_in_writeinpublic(self, m):
        # Mock WriteInPublic API
        m.get(
            '/api/v1/instance/1/messages/'.format(self.na_committee.id),
            json={'objects': []}
        )
        m.get(
            '/api/v1/instance/1/messages/'.format(self.ncop_committee.id),
            json={'objects': []}
        )

        # National Assembly committees
        response = self.client.get(
            reverse('organisation_messages', 
            kwargs={'slug': self.na_committee.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['messages'], [])

        # NCOP committee
        response = self.client.get(
            reverse('organisation_messages', 
            kwargs={'slug': self.ncop_committee.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['messages'], [])

    def test_committee_that_doesnt_exist_in_writeinpublic(self, m):
        # Mock WriteInPublic API
        m.get(
            '/api/v1/instance/1/messages/'.format(self.na_committee.id),
            status_code=404
        )
        response = self.client.get(
            reverse('organisation_messages', kwargs={'slug': self.na_committee.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['messages'], [])

    def _mock_write_in_public_messages_post(self, mock_requests):
        # Mock the POST response
        mock_requests.post('/api/v1/message/', json={
            'id': '42'
        })

    def _test_recaptcha_recipients_to_draft_steps(self):
        # GET the new message redirect
        response = self.client.get(
            reverse('writeinpublic-committees:writeinpublic-new-message'))
        self.assertRedirects(
            response, 
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'recipients'}
            )
        )

        # GET the recipients step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        self.assertContains(response, "National Assembly")
        self.assertContains(response, "NCOP")
        self.assertContains(response, "NA Test Committee")
        # Does not contain the house in brackets 
        self.assertNotContains(
            response, "NA Test Committee (National Assembly)"
        )
        self.assertContains(response, "NCOP Test Committee")

        # POST to the recipients step
        response = self.client.post(
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'recipients'}
            ), {
                'write_in_public_new_message-current_step': 'recipients',
                'recipients-persons': self.na_committee.id,
            }
        )

        self.assertRedirects(
            response, 
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'draft'}
            ))

        # GET the draft step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(
            response, "NA Test Committee (National Assembly)"
        )
        self.assertNotContains(response, "NCOP Test Comittee (NCOP)")

        # POST to the draft step
        response = self.client.post(
            reverse('writeinpublic-committees:writeinpublic-new-message-step', 
            kwargs={'step': 'draft'}), 
            {
                'write_in_public_new_message-current_step': 'draft',
                'draft-subject': 'Test subject',
                'draft-content': 'Test message',
                'draft-author_name': 'Test',
                'draft-author_email': 'test@example.com',
            }
        )
        self.assertRedirects(
            response, 
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'preview'}
            )
        )

        return response

    def _test_successful_sending_message_wizard_steps(self):
        response = self._test_recaptcha_recipients_to_draft_steps()

        # GET the preview step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        self.assertContains(
            response, "NA Test Committee (National Assembly)"
        )
        self.assertContains(
            response, "Test subject"
        )
        self.assertContains(
            response, "Test message"
        )
        self.assertContains(response, 
            "Are you happy for this message to be made public?")

        # POST to the preview step
        response = self.client.post(
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'preview'}
            ),
            {
                'write_in_public_new_message-current_step': 'preview',
                'preview-captcha_0': 'random-string',
                'preview-captcha_1': 'PASSED'
            }
        )
        self.assertRedirects(
            response,
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'done'}
            ),
            fetch_redirect_response=False
        )

        # GET the done step
        response = self.client.get(response.url)

        # Check that we're redirected to the pending message page
        self.assertRedirects(
            response,
            reverse('writeinpublic-committees:writeinpublic-pending'),
            fetch_redirect_response=False
        )

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY=None)
    def test_sending_message_wizard_steps_without_recaptcha(self, mock_requests):
        self._mock_write_in_public_messages_post(mock_requests)
        self._test_successful_sending_message_wizard_steps()

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY='test-key')
    @patch('pombola.writeinpublic.views.recaptcha_client')
    def test_sending_message_wizard_steps_with_success_recatpcha(self, mock_requests, mocked_recaptcha_client):
        mocked_recaptcha_client.verify.return_value = True
        self._mock_write_in_public_messages_post(mock_requests)
        self._test_successful_sending_message_wizard_steps()

    @override_settings(GOOGLE_RECAPTCHA_SECRET_KEY='test-key')
    @patch('pombola.writeinpublic.views.recaptcha_client')
    def test_sending_message_wizard_steps_with_failed_recatpcha(self, mock_requests, mocked_recaptcha_client):
        mocked_recaptcha_client.verify.return_value = False
        response = self._test_recaptcha_recipients_to_draft_steps()

        # GET the preview step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the preview step
        response = self.client.post(
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'preview'}
            ),
            {
                'write_in_public_new_message-current_step': 'preview',
                'preview-captcha_0': 'random-string',
                'preview-captcha_1': 'PASSED'
            },
            follow=True
        )

        # After unsuccessful Recaptcha, return to the preview page
        self.assertRedirects(
            response,
            reverse(
                'writeinpublic-committees:writeinpublic-new-message-step', 
                kwargs={'step': 'preview'}
            ),
            fetch_redirect_response=False
        )
        
        # Check that the error message is in the context
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, "error")
        expected_message = 'Sorry, there was an error sending your message, please try again. If this problem persists please contact us.'
        self.assertTrue(expected_message in message.message)


class PersonAdapterTest(TestCase):
    def test_get(self):
        adapter = PersonAdapter()
        person = Person.objects.create()
        self.assertEqual(adapter.get(person.id), person)


class CommitteeAdapterTest(TestCase):
    def test_get_form_initial(self):
        adapter = CommitteeAdapter()

        self.assertEqual(adapter.get_form_initial(step='draft', cleaned_data={}), {})
        self.assertEqual(adapter.get_form_initial(step='draft', cleaned_data={'recipients': None}), {})

        mock_committee = Mock()
        mock_committee.name = 'Test Name'
        self.assertEqual(
            adapter.get_form_initial(
                step='draft',
                cleaned_data={'recipients': {'persons': mock_committee}}
            ),
            {'content': 'Dear Test Name,\n\n'}
        )

    def test_get_form_kwargs_when_committee_has_multiple_emails(self):
        adapter = CommitteeAdapter()

        na_committee_kind = OrganisationKind.objects.create(name='National Assembly', slug='national-assembly-committees')
        email_kind = ContactKind.objects.create(name='Email', slug='email')
        committee = Organisation.objects.create(kind=na_committee_kind)
        committee.contacts.create(kind=email_kind, value='test@example.org', preferred=False)
        committee.contacts.create(kind=email_kind, value='test@example.com', preferred=False)

        form_kwargs = adapter.get_form_kwargs('recipients')
        self.assertEqual(len(form_kwargs['queryset']), 1)
        self.assertEqual(form_kwargs['queryset'][0], committee)


class RecipientFormTest(TestCase):
    def setUp(self):
        self.people = Person.objects.all()

    def test_defaults_to_multiple_choice(self):
        form = RecipientForm(queryset=self.people)
        self.assertEqual(ModelMultipleChoiceField, form.fields['persons'].__class__)
        self.assertEqual(self.people, form.fields['persons'].queryset)

    def test_multiple_choice_kwarg(self):
        form = RecipientForm(queryset=self.people, multiple=False)
        self.assertEqual(ModelChoiceField, form.fields['persons'].__class__)
        self.assertEqual(self.people, form.fields['persons'].queryset)
