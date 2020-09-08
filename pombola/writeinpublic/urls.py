from django.conf.urls import url
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

from . import views


write_message_wizard = views.WriteInPublicNewMessage.as_view(url_name='writeinpublic:writeinpublic-new-message-step')

urlpatterns = (
    url(
        r'^pending/$',
        never_cache(TemplateView.as_view(template_name='writeinpublic/pending.html')),
        name='writeinpublic-pending',
    ),
    url(
        r'^message/(?P<message_id>\d+)/$',
        views.WriteInPublicMessage.as_view(),
        name='writeinpublic-message'
    ),
    url(
        r'^(?P<step>.+)/$',
        never_cache(write_message_wizard),
        name='writeinpublic-new-message-step',
    ),
    url(
        r'^$',
        never_cache(write_message_wizard),
        name='writeinpublic-new-message',
    ),
)
