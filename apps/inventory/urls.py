"""
URL configuration for inventory app.
"""
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Device CRUD endpoints can be added here if needed
    # For now, using Django admin for CRUD
]
