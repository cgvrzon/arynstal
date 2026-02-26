# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Service
from .serializers import ServiceSerializer


class ServiceViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ServiceSerializer
    ordering_fields = ['order', 'name']

    def get_queryset(self):
        return Service.objects.filter(is_active=True)
