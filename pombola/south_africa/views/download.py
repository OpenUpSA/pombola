import os

from django.db.models import Prefetch, Q
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

import xlsx_streaming
from pombola.core.models import Contact, Organisation, Person, Position

MP_DOWNLOAD_TEMPLATE_SHEET = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "mp-download-template.xlsx"
)


def get_email_address_for_person(person):
    email_addresses = [person.email] if person.email else []
    email_addresses += [email_address.value for email_address in person.email_addresses]
    return " ".join(email_addresses)


def person_row_generator(persons):
    for person in persons:
        email = get_email_address_for_person(person)
        yield (
            person.name,
            ", ".join([cell_number.value for cell_number in person.cell_numbers]),
            get_email_address_for_person(person),
            ",".join(
                position.organisation.name for position in person.active_party_positions
            ),
        )


def get_active_positions_at_parties():
    return (
        Position.objects.currently_active()
        .filter(title__slug="member")
        .filter(organisation__kind__slug="party")
        .select_related("organisation")
    )


def get_active_persons_for_organisation(organisation):
    """
    Get all of the currently active positions at an organisation and prefetch
    their contact numbers, email addresses and party memberships.
    """
    organisation_positions = organisation.position_set.currently_active().values("id")

    party_positions = get_active_positions_at_parties()

    cell_phone_contacts = Contact.contact_number_contacts()
    email_contacts = Contact.email_contacts()

    # Get the persons from the positions
    return (
        Person.objects.filter(hidden=False)
        .filter(position__id__in=organisation_positions)
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


def download_members_xlsx(request, slug):
    organisation = get_object_or_404(Organisation, slug=slug)

    persons = get_active_persons_for_organisation(organisation)

    with open(MP_DOWNLOAD_TEMPLATE_SHEET, "rb") as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(
            person_row_generator(persons), template
        )

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=%s.xlsx" % (
        "%s-members" % slug
    )
    return response
