from rest_framework import viewsets

from ..models import Venue
from .serializer import VenueSerializer

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
