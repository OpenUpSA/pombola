from instances.models import Instance
import socket
from django.utils.deprecation import MiddlewareMixin

class FakeInstanceMiddleware:
    """
    We don't really use instances, as we're embedding sayit as an app. It
    should really be factored out, but for now, just use the default one
    created by the initial migration.
    """
    def process_request(self, request):
        request.instance, _ = Instance.objects.get_or_create(label='default')
        # We don't want to offer the ability to edit or delete
        # speeches to any users of the site at the moment, so force
        # that no user of the site is regarded as its owner.
        request.is_user_instance = False

# Which server behind load balancer served the request
class AddServerDetailsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        server_hostname = socket.gethostname()
        response['X-Server'] = server_hostname
        return response
