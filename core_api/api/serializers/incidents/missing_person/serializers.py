from rest_framework import serializers
from api.models.incidents import MissingPerson

class MissingPersonSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(
        source='reported_by.username', read_only=True
    )
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model  = MissingPerson
        fields = [
            'id', 'name', 'description', 'photo', 'photo_url',
            'reported_by', 'reported_by_username',
            'reported_at', 'is_found', 'found_at',
        ]
        read_only_fields = ['id', 'reported_by', 'reported_at', 'found_at']

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None
