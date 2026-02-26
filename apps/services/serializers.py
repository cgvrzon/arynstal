# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'icon', 'image_url',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
