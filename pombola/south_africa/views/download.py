from django.views.generic import TemplateView, View
import unicodecsv as csv
from django.http import HttpResponse
from django.db.models import Q
from pombola.core import models
from django.utils.six.moves import range
from django.http import StreamingHttpResponse


class SADownloadMembersIndex(TemplateView):
    template_name = "download/index.html"

    def get_context_data(self, **kwargs):
        context = {}

        context["house"] = "all"
        context["houses"] = models.Organisation.objects.filter(
            slug__in=["ncop", "national-assembly"]
        )

        # organisation__kind__slug='provincial-legislature',
        # TODO is 'ncop' provincial or 'provincial-legislature'?

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
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    headers = ["Name", "Party", "Cell", "Email"]
    headers = ["Name"]
    fieldnames = ["legal_name"]
    # Get persons
    rows = (
        models.Person.objects.filter(
            Q(position__organisation__slug="national-assembly")
            | Q(position__organisation__kind__slug="provincial-legislature"),
            position__title__slug="member",
        )
        .distinct()
        .values("legal_name")  # TODO: remove limit
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="somefilename.csv"'

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    return response
