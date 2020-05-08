import datetime

import unicodecsv as csv
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.six.moves import range
from django.views.generic import TemplateView, View
from django_date_extensions.fields import ApproximateDate, ApproximateDateField

import xlsx_streaming
from pombola.core import models
from pombola.core.models import Person, Position


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
    house_param = request.GET.get("house", "all")

    ncop_query = Q(organisation__kind__slug="provincial-legislature")
    na_query = Q(organisation__slug="national-assembly")
    house_query = None
    if house_param == "ncop":
        house_query = ncop_query
    elif house_param == "national-assembly":
        house_query = na_query
    else:
        house_query = ncop_query | na_query

    # First get the currently_active positions
    when = datetime.date.today()
    now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))
    positions = Position.objects.currently_active().filter(house_query).values("id")

    # Get the persons from the positions
    persons = (
        models.Person.objects.filter(hidden=False)
        .filter(position__id__in=positions)
        .distinct()
        .prefetch_related("contacts__kind")
    )

    def yield_people():
        for person in persons:
            cell = person.contacts.filter(kind__slug="cell").first()
            email = person.first_email
            yield (
                person.name,
                cell.value if cell else "",
                email if email else "",
                ",".join(party.name for party in person.parties()),
            )

    # TODO: move template to different directory?
    with open("People.xlsx", "rb") as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(
            yield_people(), template, batch_size=50
        )

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=mps.xlsx"
    return response
