# -*- coding: utf-8 -*-

from datetime import date
from mock import patch
import copy

from django.core.management import call_command
from django.test import TestCase

from pombola.za_hansard.models import Answer, Question, ParliamentaryTerm
from pombola.south_africa.models import ParliamentaryTerm

TERM = ParliamentaryTerm.objects.get_or_create(
    number=26, start_date=date(2014, 6, 1), end_date=date(2019, 5, 31)
)[0]

EXAMPLE_QUESTION = {
    "question": "Why did the chicken cross the road?",
    "answer": "To get to the other side",
    "asked_by_member": {
        "name": "Groucho Marx",
        "pa_url": "http://www.pa.org.za/person/groucho-marx/",
    },
    "source_file": {
        "url": "http://example.org/chicken-joke.docx",
        "file_path": "chicken-joke.docx",
    },
    "house": {"name": "National Assembly",},
    "answer_type": "written",
    "date": "2016-09-06",
    "year": "2016",
    "written_number": 1264,
    "oral_number": None,
    "president_number": None,
    "deputy_president_number": None,
    "url": "http://api.pmg.org.za/example-question/5678/",
    "question_to_name": "Minister of Arts and Culture",
    "intro": "Groucho Marx to ask the Minister of Arts and Culture",
    "translated": False,
    "term": TERM,
}

EXAMPLE_ANSWER = {
    "pmg_api_url": "https://api.pmg.org.za/committee-question/9117/",
    "term": TERM,
    "written_number": 1264,
    "language": "English",
    "date_published": "2018-06-05",
    "url": "https://pmg.org.za/files/RNW1264-180605.docx",
    "house": 'N',
    "date": "2016-09-06",
    "year": "2016",
    "text": "A Mid-Term Review is also planned to track progress to document progress and address identified implementation challenges",
    "processed_code": 1,
    "type": "docx",
    "document_name": "RNW1264-180605",
    "name": "",
}


class PMGAPITests(TestCase):
    def setUp(self):
        # Create non-duplicate question
        self.unique_question = Question.objects.create(
            date=date(2016, 10, 6),
            question='What is this question?',
            questionto='Manny du Preez',
            intro='What is this question?',
            askedby="Sarah George",
            identifier="",
            id_number=-1,
            house="N",
            answer_type="W",
            year=2016,
            translated=False,
            term_id=TERM.id,
            written_number=1268,
        )

    @patch(
        "pombola.za_hansard.management.commands.za_hansard_q_and_a_delete_duplicates.all_from_api"
    )
    def test_new_q_and_a_created(self, fake_all_from_api):
        # Create existing question and answer
        question = Question.objects.create(
            date=date(2016, 9, 6),
            question=EXAMPLE_QUESTION["question"],
            questionto=EXAMPLE_QUESTION["question_to_name"],
            intro=EXAMPLE_QUESTION["intro"],
            askedby="Groucho Marx",
            identifier="",
            id_number=-1,
            house="N",
            answer_type="W",
            year=2016,
            translated=False,
            term_id=TERM.id,
            written_number=1264,
        )
        answer = Answer.objects.create(**EXAMPLE_ANSWER)
        answer.pmg_api_url = "www.differenturl.com"
        answer.save()
        question.answer = answer
        question.save()

        # Return duplicate question from API
        def yield_question_with_duplicate_number_house_year(url):
            if url == "https://api.pmg.org.za/minister/":
                yield {
                    "questions_url": "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == "https://api.pmg.org.za/member/":
                return
            elif url == "http://api.pmg.org.za/minister/2/questions/":
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))

        fake_all_from_api.side_effect = yield_question_with_duplicate_number_house_year

        # Run the za_hansard_q_and_a_delete_duplicates command:
        call_command("za_hansard_q_and_a_delete_duplicates", scrape_from_pmg=True)

        # Check that old question and answer was deleted
        self.assertRaises(Question.DoesNotExist, question.refresh_from_db)
        self.assertRaises(Answer.DoesNotExist, answer.refresh_from_db)

        # Check that the unique question still exists
        self.unique_question.refresh_from_db()
        self.assertTrue(True)
