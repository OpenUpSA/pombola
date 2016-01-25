from rest_framework import serializers

from ..models import Venue


class VenueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Venue
        fields = ('id', 'url', 'name', 'slug')
