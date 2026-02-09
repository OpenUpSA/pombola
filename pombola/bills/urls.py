from django.urls import re_path as url

from pombola.bills.views import IndexView, BillListView

app_name = 'bills'

urlpatterns = [
    url( r'^$', IndexView.as_view(), name="index" ),
    url( r'^(?P<session_slug>[\w\-]+)/$', BillListView.as_view(), name="list" ),
]
