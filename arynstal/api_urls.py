# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from rest_framework.routers import DefaultRouter

from apps.projects.api_views import ProjectViewSet
from apps.services.api_views import ServiceViewSet
from apps.leads.api_views import LeadViewSet, BudgetViewSet

app_name = 'api'

router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='project')
router.register('services', ServiceViewSet, basename='service')
router.register('leads', LeadViewSet, basename='lead')
router.register('budgets', BudgetViewSet, basename='budget')

urlpatterns = router.urls
