# -*- coding: utf-8 -*-

from datetime import date
from mock import patch
import copy
from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase

from pombola.za_hansard.models import Answer, Question, QuestionParsingError
from pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper import Command, QuestionParsingException
from pombola.south_africa.models import ParliamentaryTerm
from nose.plugins.attrib import attr

EXAMPLE_QUESTION = {
    'question': 'Why did the chicken cross the road?',
    'answer': 'To get to the other side',
    'asked_by_member': {
        'name': 'Groucho Marx',
        'pa_url': 'http://www.pa.org.za/person/groucho-marx/',
    },
    'source_file': {
        'url': 'http://example.org/chicken-joke.docx',
        'file_path': 'chicken-joke.docx',
    },
    'house': {
        'name': 'National Assembly',
    },
    'answer_type': 'written',
    'date': '2016-09-06',
    'year': '2016',
    'written_number': 12345,
    'oral_number': None,
    'president_number': None,
    'deputy_president_number': None,
    'url': 'http://api.pmg.org.za/example-question/5678/',
    'question_to_name': 'Minister of Arts and Culture',
    'intro': 'Groucho Marx to ask the Minister of Arts and Culture',
    'translated': False,
}


@attr(country='south_africa')
class PMGAPITests(TestCase):

    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_new_q_and_a_created(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        # Assertions about the question first:
        self.assertEqual(
            question.question, 'Why did the chicken cross the road?')
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.identifier, '')
        self.assertEqual(question.id_number, -1)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date, date(2016, 9, 6))
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.askedby, 'Groucho Marx')
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url,
                         'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url,
                         'http://example.org/chicken-joke.docx')
        # Then asertions about the answer:
        self.assertEqual(answer.text, 'To get to the other side')
        self.assertEqual(answer.document_name, 'chicken-joke')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.oral_number, None)
        self.assertEqual(answer.president_number, None)
        self.assertEqual(answer.dp_number, None)
        self.assertEqual(answer.date, date(2016, 9, 6))
        self.assertEqual(answer.year, 2016)
        self.assertEqual(answer.house, 'N')
        self.assertEqual(answer.processed_code, Answer.PROCESSED_OK)
        self.assertEqual(answer.name, '')
        self.assertEqual(answer.language, 'English')
        self.assertEqual(answer.url, 'http://example.org/chicken-joke.docx')
        self.assertEqual(answer.date_published, date(2016, 9, 6))
        self.assertEqual(answer.type, 'docx')
        self.assertEqual(answer.sayit_section, None)
        self.assertEqual(answer.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')

    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_only_new_answer_if_question_exists(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing question with the right year and
        # written_number; this test makes sure that a duplicate
        # question isn't created in that circumstance.
        Question.objects.create(
            question=u'Forsooth, why hath the chicken crossèd the road?',
            written_number=12345,
            date=date(2016, 1, 27),
            house='N',
            answer_type='W',
            term=ParliamentaryTerm.objects.get(number=26),
            year=2016,
            identifier='NW9876543E',
            id_number='9876543',
            askedby='G Marx',
            translated=False,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        # It should have the old question text, identifier and askedby
        # still, in particular:
        self.assertEqual(
            question.question,
            u'Forsooth, why hath the chicken crossèd the road?')
        self.assertEqual(question.askedby, 'G Marx')
        self.assertEqual(question.identifier, 'NW9876543E')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 1, 27))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url,
                         'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url,
                         'http://example.org/chicken-joke.docx')

    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_create_question_if_questions_have_different_terms(self, fake_all_from_api):
        new_term_question = copy.deepcopy(EXAMPLE_QUESTION)
        new_term_question['year'] = '2019'
        new_term_question['date'] = '2019-06-03' # 27th term
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield new_term_question
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer

        # Create an existing question with the same year and written_number,
        # but in a different term.

        question = Question.objects.create(
            question=u'Forsooth, why hath the chicken crossèd the road?',
            written_number=12345,
            date=date(2019, 1, 27), # 26th term
            term=ParliamentaryTerm.objects.get(number=26),
            house='N',
            answer_type='W',
            year=2019,
            identifier='NW9876543E',
            id_number='9876543',
            askedby='G Marx',
            translated=False,
        )
        answer = Answer.objects.create(
            written_number=12345,
            date=date(2019, 1, 27), # 26th term
            date_published=date(2019, 1, 27),
            term=ParliamentaryTerm.objects.get(number=26),
            house='N',
            type='W',
            year=2019,
            language='English',
            text='It is true.'
        )
        question.answer = answer


        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)

        # Check that a new question was created even though the year and 
        # written_number is the same.

        # Check that what we expect has been created:
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Answer.objects.count(), 2)


    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_nothing_created_if_both_exist(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing question and answer with the right year
        # and written_number; this test makes sure neither a new
        # question nor a new answer is created in this case:
        existing_answer = Answer.objects.create(
            text='For to arrive unto the other side',
            written_number=12345,
            date=date(2016, 9, 1),
            term=ParliamentaryTerm.objects.get(number=26),
            date_published=date(2016, 9, 6),
            year=2016,
            house='N',
            processed_code=Answer.PROCESSED_OK,
        )
        Question.objects.create(
            question=u'Forsooth, why hath the chicken crossèd the road?',
            answer=existing_answer,
            written_number=12345,
            date=date(2016, 1, 27),
            term=ParliamentaryTerm.objects.get(number=26),
            house='N',
            answer_type='W',
            year=2016,
            identifier='NW9876543E',
            id_number='9876543',
            askedby='G Marx',
            translated=False,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        self.assertEqual(question.answer, answer)
        # It should have the old question text, identifier and askedby
        # still, in particular:
        self.assertEqual(
            question.question,
            u'Forsooth, why hath the chicken crossèd the road?')
        self.assertEqual(question.askedby, 'G Marx')
        self.assertEqual(question.identifier, 'NW9876543E')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 1, 27))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url,
                         'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url,
                         'http://example.org/chicken-joke.docx')
        # Now check that the answer still has some old values:
        self.assertEqual(answer.text, 'For to arrive unto the other side')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.date, date(2016, 9, 1))
        self.assertEqual(answer.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')

    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_question_created_if_answer_exists(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing answer with the right year and
        # written_number, but no corresponding existing question.
        Answer.objects.create(
            text='For to arrive unto the other side',
            written_number=12345,
            date=date(2016, 9, 1),
            term=ParliamentaryTerm.objects.get(number=26),
            date_published=date(2016, 9, 6),
            year=2016,
            house='N',
            processed_code=Answer.PROCESSED_OK,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        self.assertEqual(question.answer, answer)
        # It should have the new question text
        self.assertEqual(
            question.question,
            u'Why did the chicken cross the road?')
        self.assertEqual(question.askedby, 'Groucho Marx')
        self.assertEqual(question.identifier, '')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 9, 6))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url,
                         'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url,
                         'http://example.org/chicken-joke.docx')
        # Now check that the answer still has some old values:
        self.assertEqual(answer.text, 'For to arrive unto the other side')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.date, date(2016, 9, 1))
        self.assertEqual(answer.pmg_api_url,
                         'http://api.pmg.org.za/example-question/5678/')

    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    @patch('pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper.sys.exit')
    def test_errors_logged_to_model(self, fake_sys_exit, fake_all_from_api):
        question_with_invalid_date = copy.deepcopy(EXAMPLE_QUESTION)
        question_with_invalid_date['date'] = '2012319-06-03' # invalid date
        question_with_invalid_parliamentary_term = copy.deepcopy(EXAMPLE_QUESTION)
        question_with_invalid_parliamentary_term['date'] = '2035-06-03'
        question_without_number = copy.deepcopy(EXAMPLE_QUESTION)
        del question_without_number['written_number']
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield question_with_invalid_date
                yield question_with_invalid_parliamentary_term
                yield question_without_number
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer

        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True, verbosity=4)

        # Check that no new questions or answers were created
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        # Check that QuestionParsingErrors were created
        self.assertEqual(QuestionParsingError.objects.count(), 3)
        self.assertTrue(QuestionParsingError.objects.filter(error_type='date-format-error').exists())
        self.assertTrue(QuestionParsingError.objects.filter(error_type='term-not-found').exists())
        self.assertTrue(QuestionParsingError.objects.filter(error_type='number-not-found').exists())

        fake_sys_exit.assert_called_with(1)


@attr(country='south_africa')
class ParsePmgQuestionDataTests(TestCase):
    def setUp(self):
        self.command = Command()

    def test_valid_parse_example_question(self):
        expected = {
            "written_number": 12345,
            "house": "N",
            "number_found": True,
            "existing_kwargs": {
                "house": "N",
                "term": ParliamentaryTerm.objects.get(number=26),
                "written_number": 12345,
                "date__year": "2016",
            },
            "source_file": {
                "url": "http://example.org/chicken-joke.docx",
                "file_path": "chicken-joke.docx",
            },
            "number_q_kwargs": {"written_number": 12345},
            "year": "2016",
            "president_number": None,
            "question_text": "Why did the chicken cross the road?",
            "answer_type": "W",
            "deputy_president_number": None,
            "intro": "Groucho Marx to ask the Minister of Arts and Culture",
            "question_to_name": "Minister of Arts and Culture",
            "question_date": date(2016, 9, 6),
            "answer": "To get to the other side",
            "date": "2016-09-06",
            "term": ParliamentaryTerm.objects.get(number=26),
            "url": "http://api.pmg.org.za/example-question/5678/",
            "askedby_name": "Groucho Marx",
            "translated": False,
            "oral_number": None,
            "askedby_pa_url": "http://www.pa.org.za/person/groucho-marx/",
        }
        result = self.command.parse_pmg_question_data(EXAMPLE_QUESTION)

        self.assertEqual(expected, result)

    def test_no_source_file(self):
        question = {}
        with self.assertRaisesRegexp(QuestionParsingException, 'missing'):
            result = self.command.parse_pmg_question_data(question)
        
    def test_unsupported_house(self):
        question = copy.deepcopy(EXAMPLE_QUESTION)
        question['house']['name'] = 'unsupported'
        with self.assertRaisesRegexp(QuestionParsingException, 'unsupported'):
            result = self.command.parse_pmg_question_data(question)

    def test_ncop_house(self):
        question = copy.deepcopy(EXAMPLE_QUESTION)
        question['house']['name'] = u'National Council of Provinces'
        result = self.command.parse_pmg_question_data(question)
        self.assertIs(dict, type(result))
        self.assertEqual(result['existing_kwargs']['house'], 'C')

    def test_unsupported_answer_type(self):
        question = copy.deepcopy(EXAMPLE_QUESTION)
        question['answer_type'] = 'unsupported'
        with self.assertRaisesRegexp(QuestionParsingException, 'answer type'):
            result = self.command.parse_pmg_question_data(question)

    def test_invalid_term_date(self):
        question = copy.deepcopy(EXAMPLE_QUESTION)
        question['date'] = '1990-02-20'
        with self.assertRaisesRegexp(QuestionParsingException, 'Could not determine the parliamentary term'):
            result = self.command.parse_pmg_question_data(question)

    def test_invalid_date(self):
        question = copy.deepcopy(EXAMPLE_QUESTION)
        question['date'] = 'not-a-date'
        with self.assertRaisesRegexp(QuestionParsingException, 'Could not parse the date'):
            result = self.command.parse_pmg_question_data(question)