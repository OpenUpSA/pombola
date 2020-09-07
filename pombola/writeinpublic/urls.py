from django.conf.urls import url
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page

from . import views


write_message_wizard = views.WriteInPublicNewMessage.as_view(url_name='writeinpublic:writeinpublic-new-message-step')

urlpatterns = (
    url(
        r'^pending/$',
        cache_page(0)(TemplateView.as_view(template_name='writeinpublic/pending.html')),
        name='writeinpublic-pending',
    ),
    url(
        r'^message/(?P<message_id>\d+)/$',
        cache_page(0)(views.WriteInPublicMessage.as_view()),
        name='writeinpublic-message'
    ),
    url(
        r'^(?P<step>.+)/$',
        cache_page(0)(write_message_wizard),
        name='writeinpublic-new-message-step',
    ),
    url(
        r'^$',
        cache_page(0)(write_message_wizard),
        name='writeinpublic-new-message',
    ),
)
