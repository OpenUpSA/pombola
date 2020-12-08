from django.template import RequestContext
from django.shortcuts import render, get_object_or_404

import pombola.core.models


def in_place(request, slug):

    place = get_object_or_404( pombola.core.models.Place, slug=slug)
    projects = place.project_set

    return render(
        request,
        'projects/in_place.html',
        {
            'place': place,
            'projects': projects,
        },
    )

