import os

from django.db.models import Prefetch, Q
from django.http import StreamingHttpResponse
from django.views.generic import TemplateView

import xlsx_streaming
from pombola.core.models import Contact, Organisation, Person, Position

MP_DOWNLOAD_TEMPLATE_SHEET = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "mp-download-template.xlsx"
)


def generate_sheet_name(house=None):
    """
    Generate the sheet name of the file that will be downloaded using the house.
    """
    if house and house != "all":
        return house + "-members"
    return "members-of-parliament"


def get_organisation_query_filter_for_house(house="all"):
    """
    Get the query to filter the organisations by given the house.
    """
    ncop_query = Q(organisation__kind__slug="provincial-legislature")
    na_query = Q(organisation__slug="national-assembly")

    if house == "ncop":
        return ncop_query
    elif house == "national-assembly":
        return na_query
    else:
        return ncop_query | na_query


def download_members_xlsx(request):
    house_param = request.GET.get("house", "all")
    house_query = get_organisation_query_filter_for_house(house_param)

    # Get all of the currently_active positions at the houses
    house_positions = (
        Position.objects.currently_active().filter(house_query).values("id")
    )

    party_positions = (
        Position.objects.currently_active()
        .filter(title__slug="member")
        .filter(organisation__kind__slug="party")
        .select_related("organisation")
    )

    cell_phone_contacts = Contact.contact_number_contacts()
    email_contacts = Contact.email_contacts()

    # Get the persons from the positions
    persons = (
        Person.objects.filter(hidden=False)
        .filter(position__id__in=house_positions)
        .distinct()
        .prefetch_related(
            "alternative_names",
            Prefetch(
                "position_set",
                queryset=party_positions,
                to_attr="active_party_positions",
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

    def person_row_generator():
        for person in persons:
            email = get_email_address_for_person(person)
            yield (
                person.name,
                person.cell_numbers[0].value if len(person.cell_numbers) > 0 else "",
                get_email_address_for_person(person),
                ",".join(
                    position.organisation.name
                    for position in person.active_party_positions
                ),
            )

    with open(MP_DOWNLOAD_TEMPLATE_SHEET, "rb") as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(person_row_generator(), template)

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response[
        "Content-Disposition"
    ] = "attachment; filename=%s.xlsx" % generate_sheet_name(house_param)
    return response
