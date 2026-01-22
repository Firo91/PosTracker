"""
URL configuration for netwatch project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from apps.monitoring.api_views import agent_report

# Restrict admin access to authenticated users
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path('accounts/', include('apps.accounts.urls')),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', include('apps.dashboard.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('api/agent-report/', agent_report, name='agent_report'),
]

# Customize admin site
admin.site.site_header = 'NetWatch Administration'
admin.site.site_title = 'NetWatch Admin'
admin.site.index_title = 'Device Monitoring Dashboard'
