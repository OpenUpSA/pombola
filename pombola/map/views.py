from django.shortcuts  import render
from django.template   import RequestContext

def home(request):
    """Homepage"""

    return render(
        request,
        'map/home.html',
        {},
    )

