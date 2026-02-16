from django.shortcuts  import render

def home(request):
    """Homepage"""

    return render(
        request,
        'map/home.html',
        {},
    )

