"""
Once-off command to delete all of the questions and answers that were incorrectly
identified as duplicates. This would probably only ever need to be run once and 
never again.

Previously we didn't take the term into account when identifying questions that 
we scrape from PMG. Then questions that are in the same year and that have the
same number, but in different terms were identified as duplicates. We now use 
the same logic to find all of those questions and delete them before running
the scraper again to fetch them again from PMG.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

import re
import requests

from pombola.za_hansard.models import Question, Answer, QuestionPaper
from pombola.za_hansard.importers.import_json import ImportJson


ANSWER_TYPES = {"written": "W"}


def all_from_api(start_url):
    next_url = start_url
    while next_url:
        r = requests.get(next_url)
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException:
            print "Error while fetching", next_url
            raise
        data = r.json()
        for member in data["results"]:
            yield member
        next_url = data["next"]


def convert_url_to_https(url):
    return re.sub(r"^http:", "https:", url)


class Command(BaseCommand):

    help = "Delete previously duplicate hansard questions and answers"

    def handle(self, *args, **options):
        self.delete_old_duplicate_questions_and_answers(*args, **options)

    def delete_old_duplicate_questions_and_answers(self, *args, **options):
        # Go through each member and minister looking for questions
        # URLs.
        for url in (
            "https://api.pmg.org.za/minister/",
            "https://api.pmg.org.za/member/",
        ):
            for m in all_from_api(url):
                questions_url = m["questions_url"]
                for question in all_from_api(questions_url):
                    with transaction.atomic():
                        self.handle_api_question_and_reply(question)

    def handle_api_question_and_reply(self, data):
        if "source_file" not in data:
            print "Skipping {0} due to a missing source_file".format(data["url"])
            return
        house = {"National Assembly": "N"}[data["house"]["name"]]
        if data["answer_type"] not in ANSWER_TYPES:
            print "Skipping {} because the answer type {} is not supported".format(
                data["url"], data["answer_type"]
            )
            return
        answer_type = ANSWER_TYPES[data["answer_type"]]
        askedby_name = ""
        askedby_pa_url = ""
        if "asked_by_member" in data:
            askedby_name = data["asked_by_member"]["name"]
            if "pa_url" in data["asked_by_member"]:
                askedby_pa_url = data["asked_by_member"]["pa_url"]
        question_text = data["question"]
        # 'code' is one of those like: "NW3847", but in the Code4SA /
        # PMG API data that's just composed (say) of 'NW' + the
        # written_number; they don't match with the NW codes that
        # questions already have in our data. So we can't use the
        # 'code' field for checking if the question already exists, so
        # try to identify a unique question by the number + year +
        # house. (The numbers reset each year.)
        year = data["date"][:4]
        # Add whatever number there is to the query:
        number_q_kwargs = {}
        number_found = False
        for filter_key, api_key in (
            ("written_number", "written_number"),
            ("oral_number", "oral_number"),
            ("president_number", "president_number"),
            ("dp_number", "deputy_president_number"),
        ):
            if data[api_key]:
                number_found = True
                number_q_kwargs[filter_key] = data[api_key]

        existing_kwargs = {"date__year": year, "house": house}
        existing_kwargs.update(number_q_kwargs)
        question = None
        if not number_found:
            # We won't be able to accurately tell whether a question
            # already exists if we don't have one of these number, so
            # ignore the question and answer completely in that
            # case. (This is a rare occurence.)
            print "Skipping {0} because no number was found".format(data["url"])
            return
        question_query =  Question.objects.filter(**existing_kwargs)
        if question_query.exists():
            print("Found the existing question for %s" % data["url"])
        else:
            return

        for question in question_query:
            # Check if there is an existing answer
            if question.answer:
                print "That question already had an answer. Checking if it's the same one."
                answer = question.answer
                existing_answer_pmg_api_url = answer.pmg_api_url
                if existing_answer_pmg_api_url and convert_url_to_https(
                    existing_answer_pmg_api_url
                ) != convert_url_to_https(data["url"]):
                    msg = "An existing answer's pmg_api_url conflicted "
                    msg += "with another one from the API. In the database, "
                    msg += "the question ID was {0}, the answer ID was {1}, "
                    msg += "and the PMG API URL was {2}. The new PMG API URL "
                    msg += "was {3}. Deleting question and answer."
                    print msg.format(
                        question.id, answer.id, existing_answer_pmg_api_url, data["url"]
                    )
                    answer.delete()
                    question.delete()
                else:
                    print "Answer is the same."
