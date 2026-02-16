from django.urls import re_path as url

from pombola.map.views import home


urlpatterns = [
    url(r'^$', home, name='map-home'),
]
