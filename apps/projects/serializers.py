# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from rest_framework import serializers

from .models import Project, ProjectImage


class ProjectImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = ['id', 'url', 'alt_text', 'order']

    def get_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class ProjectListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', default=None)
    service_slug = serializers.CharField(source='service.slug', default=None)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'service_name', 'service_slug',
            'cover_image_url', 'year', 'is_featured',
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url)
        return obj.cover_image.url if obj.cover_image else None


class ProjectDetailSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', default=None)
    service_slug = serializers.CharField(source='service.slug', default=None)
    cover_image_url = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    additional_images = ProjectImageSerializer(source='images', many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'description', 'service_name',
            'service_slug', 'cover_image_url', 'area', 'duration',
            'year', 'client', 'is_featured', 'details', 'images',
            'additional_images',
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url)
        return obj.cover_image.url if obj.cover_image else None

    def get_details(self, obj):
        return obj.get_details_list()

    def get_images(self, obj):
        request = self.context.get('request')
        urls = obj.get_all_image_urls()
        if request:
            return [request.build_absolute_uri(url) for url in urls]
        return urls
