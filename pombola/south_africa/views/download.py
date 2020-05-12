import os

from django.db.models import Prefetch, Q
from django.http import StreamingHttpResponse
from django.views.generic import TemplateView

import xlsx_streaming
from pombola.core.models import Contact, Organisation, Person, Position


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
    positions = Position.objects.currently_active().filter(house_query).values("id")

    parties = (
        Position.objects.currently_active()
        .filter(title__slug="member")
        .filter(organisation__kind__slug="party")
        .select_related("organisation")
    )

    cell_phone_contacts = Contact.objects.filter(kind__slug__in=["cell", "phone"])
    email_contacts = Contact.objects.filter(kind__slug__in=["email"])

    # Get the persons from the positions
    persons = (
        Person.objects.filter(hidden=False)
        .filter(position__id__in=positions)
        .distinct()
        .prefetch_related(
            "alternative_names",
            Prefetch(
                "position_set", queryset=parties, to_attr="active_party_positions"
            ),
            Prefetch("contacts", queryset=cell_phone_contacts, to_attr="cell_numbers"),
            Prefetch("contacts", queryset=email_contacts, to_attr="email_addresses"),
        )
    )

    def get_email_address_for_person(person):
        if person.email:
            return person.email
        if len(person.email_addresses) > 0:
            return person.email_addresses[0].value
        return ""

    def yield_people():
        for person in persons:
            email = (
                person.email
                if person.email
                else (
                    person.email_addresses[0].value
                    if len(person.email_addresses) > 0
                    else ""
                )
            )
            yield (
                person.name,
                person.cell_numbers[0].value if len(person.cell_numbers) > 0 else "",
                get_email_address_for_person(person),
                ",".join(
                    position.organisation.name
                    for position in person.active_party_positions
                ),
            )

    with open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "mp-download-template.xlsx"
        ),
        "rb",
    ) as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(
            yield_people(), template, batch_size=50
        )

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response[
        "Content-Disposition"
    ] = "attachment; filename=%s.xlsx" % generate_sheet_name(house_param)
    return response


def generate_sheet_name(house=None):
    if house and house != "all":
        return house + "-members"
    return "members-of-parliament"
