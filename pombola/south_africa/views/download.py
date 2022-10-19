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


def get_email_addresses_for_person(person):
    """
    Return all of the email addresses that we have for a person separated by spaces.
    """
    email_addresses = [person.email] if person.email else []
    email_addresses += [email_address.value for email_address in person.email_addresses]
    return " ".join(email_addresses)


def person_row_generator(persons):
    """
    Generate a tuple for each person containing their name, contact numbers, 
    email addresses and party memberships.
    """
    for person in persons:
        email = get_email_addresses_for_person(person)
        yield (
            # Name
            person.name,
            # Contact numbers
            ", ".join([contact_number.value for contact_number in person.contact_numbers]),
            # Email addresses
            get_email_addresses_for_person(person),
            # Parties
            ",".join(
                position.organisation.name for position in person.active_party_positions
            ),
            # Twitter 
            ", ".join([contact.value for contact in person.twitter_contacts]),
            # Facebook
            ", ".join([contact.value for contact in person.facebook_contacts]),
            # LinkedIn
            ", ".join([contact.value for contact in person.linkedin_contacts]),
            # Instagram
            ", ".join([contact.value for contact in person.instagram_contacts]),
        )


def get_active_persons_for_organisation(organisation):
    """
    Get all of the currently active positions at an organisation.
    """
    organisation_positions = organisation.position_set.currently_active().values("id")

    # Get the persons from the positions
    return (
        Person.objects.filter(hidden=False)
        .filter(position__id__in=organisation_positions)
        .distinct()
    )


def get_queryset_for_members_download(organisation):
    """
    Return the querset for the members download with the necessary data prefetched.
    """
    return (
        get_active_persons_for_organisation(organisation)
        .prefetch_contact_numbers()
        .prefetch_email_addresses()
        .prefetch_active_party_positions()
        .prefetch_contacts_with_kind('twitter')
        .prefetch_contacts_with_kind('facebook')
        .prefetch_contacts_with_kind('linkedin')
        .prefetch_contacts_with_kind('instagram')
        .prefetch_related("alternative_names",)
    )


def download_members_xlsx(request, slug):
    """
    View function to stream an Excel sheet containing people's contact details
    for people who are active members of an organisation with the given slug.
    """
    organisation = get_object_or_404(Organisation, slug=slug)

    persons = get_queryset_for_members_download(organisation)

    with open(MP_DOWNLOAD_TEMPLATE_SHEET, "rb") as template:
        stream = xlsx_streaming.stream_queryset_as_xlsx(
            person_row_generator(persons), template
        )

    response = StreamingHttpResponse(
        stream,
        content_type="application/vnd.xlsxformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=%s-members.xlsx" % organisation.slug
    return response
