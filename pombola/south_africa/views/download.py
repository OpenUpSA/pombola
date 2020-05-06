from django.views.generic import TemplateView, View
import unicodecsv as csv
from django.http import HttpResponse
from django.db.models import Q
from pombola.core import models
from pombola.core.models import Person, Position
from django.utils.six.moves import range
from django_date_extensions.fields import ApproximateDateField, ApproximateDate
import datetime
from django.http import StreamingHttpResponse

import xlsx_streaming


class SADownloadMembersIndex(TemplateView):
    template_name = "download/index.html"

    def get_context_data(self, **kwargs):
        context = {}

        context["selected_house"] = "all"
        context["houses"] = [
            {"name": "All", "slug": "all"},
            {"name": "NCOP", "slug": "ncop"},
            {"name": "National Assembly", "slug": "national-assembly"},
        ]

        return context


def download_members_xlsx(request):
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    headers = ["Name", "Party", "Cell", "Email"]
    headers = ["Name", "Cell", "Email"]
    fieldnames = ["legal_name", "cell", "email"]
    house_query = None
    house_param = request.GET.get("house", "all")

    # Get their first cell
    #  person.contacts.all()[1].kind.slug = 'cell'
    # Get their first email
    #  person.contacts.all()[1].kind.slug = 'email'
    # could also be
    # person.email

    ncop_query = Q(organisation__kind__slug="provincial-legislature")
    na_query = Q(organisation__slug="national-assembly")
    if house_param == "ncop":
        house_query = ncop_query
    elif house_param == "national-assembly":
        house_query = na_query
    else:
        house_query = ncop_query | na_query

    # First get the currently_active positions
    when = datetime.date.today()
    now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))
    positions = (
        Position.objects.filter(
            sorting_start_date__lte=now_approx
        )  # TODO: move to model
        .filter(Q(sorting_end_date_high__gte=now_approx) | Q(end_date=""))
        .filter(house_query)
        .values("id")
    )

    # TODO: check person not hidden
    # Get the persons from the positions
    persons = (
        models.Person.objects.filter(position__id__in=positions)
        .distinct()
        .prefetch_related("contacts__kind")
    )

    def get_person_email(person):
        if person.email:
            return person.email
        contact_email = person.contacts.filter(kind__slug="email").first()
        if contact_email:
            return contact_email.value
        return ""

    def yield_people():
        for person in persons:
            cell = person.contacts.filter(kind__slug="cell").first()
            email = get_person_email(person)
            yield (
                person.name,
                cell.value if cell else "",
                get_person_email(person),
                ",".join(party.name for party in person.parties()),
            )

    # TODO: move template to different directory
    with open("People.xlsx", "rb") as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(
            yield_people(), template, batch_size=50
        )

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=test.xlsx"
    return response
