# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from rest_framework.permissions import BasePermission


class IsAdminOrOffice(BasePermission):
    """Permite acceso a usuarios con rol admin u office."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
        return profile.can_manage_leads()


class IsFieldTechnician(BasePermission):
    """Permite acceso a cualquier usuario autenticado con perfil válido."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile')


class CanUpdateLead(BasePermission):
    """
    Object-level permission:
    - admin/office pueden actualizar cualquier lead
    - field solo puede actualizar leads asignados a él
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        profile = request.user.profile
        if profile.can_manage_leads():
            return True
        return obj.assigned_to == request.user
