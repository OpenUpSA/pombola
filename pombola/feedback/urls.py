from django.urls import re_path as url

from .views import add


urlpatterns = [
    url(r'^$', add, name='feedback_add'),
]
