# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
import re

from rest_framework import serializers

from .models import Lead, LeadLog, Budget


# =============================================================================
# FASE 2: Creación pública de leads
# =============================================================================

class CreateLeadSerializer(serializers.ModelSerializer):
    website_url = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        default='',
    )

    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'phone', 'location', 'service',
            'message', 'preferred_contact', 'urgency', 'website_url',
        ]

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'El nombre debe tener al menos 3 caracteres.'
            )
        return value.strip()

    def validate_phone(self, value):
        digits = re.sub(r'\D', '', value)
        if not (9 <= len(digits) <= 15):
            raise serializers.ValidationError(
                'El teléfono debe tener entre 9 y 15 dígitos.'
            )
        return value

    def validate_message(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                'El mensaje debe tener al menos 20 caracteres.'
            )
        if len(value) > 1000:
            raise serializers.ValidationError(
                'El mensaje no puede superar los 1000 caracteres.'
            )
        return value.strip()


# =============================================================================
# FASE 3: Endpoints autenticados
# =============================================================================

class LeadListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', default=None)
    assigned_to_name = serializers.SerializerMethodField()
    images_count = serializers.IntegerField(read_only=True)
    budgets_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone', 'location', 'service',
            'service_name', 'message', 'source', 'status',
            'assigned_to', 'assigned_to_name', 'notes',
            'preferred_contact', 'urgency',
            'images_count', 'budgets_count',
            'created_at', 'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None


class LeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['status', 'notes', 'assigned_to']


class LeadLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadLog
        fields = ['id', 'action', 'old_value', 'new_value', 'user_name', 'created_at']

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class BudgetListSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'reference', 'description', 'amount', 'status',
            'valid_until', 'lead', 'lead_name',
            'created_by', 'created_by_name', 'created_at',
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
