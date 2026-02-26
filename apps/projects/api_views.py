# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from django_filters import rest_framework as filters
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Project
from .serializers import ProjectListSerializer, ProjectDetailSerializer


class ProjectFilter(filters.FilterSet):
    service = filters.CharFilter(field_name='service__slug', lookup_expr='exact')
    year = filters.NumberFilter(field_name='year')
    is_featured = filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model = Project
        fields = ['service', 'year', 'is_featured']


class ProjectViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = ProjectFilter
    ordering_fields = ['year', 'order', 'created_at']
    lookup_field = 'pk'

    def get_queryset(self):
        return (
            Project.objects
            .filter(is_active=True)
            .select_related('service')
            .prefetch_related('images')
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectListSerializer
