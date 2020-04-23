from django.views.generic import TemplateView, View
import unicodecsv as csv
from django.http import HttpResponse
from django.db.models import Q
from pombola.core import models
from django.utils.six.moves import range
from django_date_extensions.fields import ApproximateDateField, ApproximateDate
import datetime
from django.http import StreamingHttpResponse


class SADownloadMembersIndex(TemplateView):
    template_name = "download/index.html"

    def get_context_data(self, **kwargs):
        context = {}

        context["selected_house"] = "all"
        context["houses"] = [
            {'name': "All", 'slug': "all"},
            {'name': "NCOP", 'slug': "ncop"},
            {'name': "National Assembly", 'slug': "national-assembly"},
        ]

        return context


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def download_members_csv(request):
    """A view that streams a large CSV file."""
    #  TODO: check that request is GET
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    headers = ["Name", "Party", "Cell", "Email"]
    headers = ["Name", "Cell", "Email"]
    fieldnames = ["legal_name", 'cell', 'email']
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
    
    # TODO: filter by currently_active
    # TODO: get the persons' party
    # {'kind__slug': u'party' 

    # First get the currently_active positions
    when = datetime.date.today()
    now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))
    positions = models.Position.objects \
        .filter(sorting_start_date__lte=now_approx) \
        .filter(Q(sorting_end_date_high__gte=now_approx) | Q(end_date='')) \
        .filter(house_query) \
        .values('id')

    # Get the persons from the positions
    persons = models.Person.objects.filter(position__id__in=positions).distinct() \
        .prefetch_related('contacts__kind')

    # TODO: get the person's parties
    rows = []
    for person in persons:
        cell = person.contacts.filter(kind__slug='cell').first()
        email = person.contacts.filter(kind__slug='email').first()
        rows.append(
            {
                'legal_name': person.legal_name,
                'cell': cell.value if cell else '',
                'email': email.value if email else '',
            }
        )

    # Get persons
    # rows = (
    #     models.Person.objects.filter(house_query, position__title__slug="member",)
    #     .distinct()
    #     .values("legal_name")  # TODO: remove limit
    # )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="somefilename.csv"'

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    return response
