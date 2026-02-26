# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from django.db.models import Count

from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from apps.web.views import get_client_ip

from .models import Lead, Budget
from .permissions import IsAdminOrOffice, IsFieldTechnician, CanUpdateLead
from .serializers import (
    CreateLeadSerializer,
    LeadListSerializer,
    LeadUpdateSerializer,
    LeadLogSerializer,
    BudgetListSerializer,
)


class LeadFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status')
    source = filters.CharFilter(field_name='source')
    service = filters.NumberFilter(field_name='service_id')
    assigned_to = filters.NumberFilter(field_name='assigned_to_id')
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = Lead
        fields = ['status', 'source', 'service', 'assigned_to']


class LeadViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filterset_class = LeadFilter
    ordering_fields = ['created_at', 'updated_at', 'status']
    throttle_scope = None

    def get_throttles(self):
        if self.action == 'create':
            from rest_framework.throttling import ScopedRateThrottle
            throttle = ScopedRateThrottle()
            throttle.scope = 'lead_create'
            return [throttle]
        return super().get_throttles()

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ('list', 'retrieve'):
            return [IsFieldTechnician()]
        if self.action == 'partial_update':
            return [CanUpdateLead()]
        if self.action == 'logs':
            return [IsAdminOrOffice()]
        return [IsFieldTechnician()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateLeadSerializer
        if self.action == 'partial_update':
            return LeadUpdateSerializer
        if self.action == 'logs':
            return LeadLogSerializer
        return LeadListSerializer

    def get_queryset(self):
        qs = (
            Lead.objects
            .select_related('service', 'assigned_to')
            .annotate(
                images_count=Count('images', distinct=True),
                budgets_count=Count('budgets', distinct=True),
            )
            .order_by('-created_at')
        )
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        profile = getattr(user, 'profile', None)
        if profile and profile.can_manage_leads():
            return qs
        return qs.filter(assigned_to=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Honeypot check
        if serializer.validated_data.pop('website_url', ''):
            return Response(
                {'detail': 'Solicitud recibida correctamente.'},
                status=status.HTTP_201_CREATED,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        lead = serializer.save(
            status='nuevo',
            source='api',
            privacy_accepted=True,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        # Notificaciones async con fallback síncrono
        try:
            from apps.leads.tasks import send_new_lead_notifications
            send_new_lead_notifications.delay(lead.id)
        except Exception:
            from apps.leads.notifications import notify_new_lead
            notify_new_lead(lead)

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        lead = self.get_object()
        logs_qs = lead.logs.select_related('user').all()
        page = self.paginate_queryset(logs_qs)
        if page is not None:
            serializer = LeadLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = LeadLogSerializer(logs_qs, many=True)
        return Response(serializer.data)


class BudgetViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAdminOrOffice]
    serializer_class = BudgetListSerializer
    ordering_fields = ['created_at', 'amount', 'status']

    def get_queryset(self):
        return Budget.objects.select_related('lead', 'created_by').all()
