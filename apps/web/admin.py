"""
La app 'web' no tiene modelos propios, por lo tanto no tiene configuración de admin.

Las configuraciones de admin están en:
- apps.leads.admin: Lead, LeadImage, Budget, LeadLog
- apps.services.admin: Service
- apps.users.admin: User (extendido con UserProfile)
- apps.contact.admin: ContactMessage
"""

from django.contrib import admin

# Personalización global del sitio admin
admin.site.site_header = "Arynstal SL - Administración"
admin.site.site_title = "Arynstal Admin"
admin.site.index_title = "Panel de control"
