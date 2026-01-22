"""
URL configuration for dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/manage/', views.manage_units, name='manage_units'),
    path('units/<int:unit_id>/', views.unit_detail, name='unit_detail'),
    path('device/<int:device_id>/', views.device_detail_view, name='device_detail'),
    path('add/', views.add_device_view, name='add_device'),
    path('tokens/', views.manage_api_tokens, name='manage_tokens'),
    path('tokens/create/', views.create_api_token, name='create_token'),
    path('tokens/<int:token_id>/delete/', views.delete_api_token, name='delete_token'),
    path('tokens/<int:token_id>/toggle/', views.toggle_api_token, name='toggle_token'),
    path('device/<int:device_id>/edit/', views.edit_device, name='edit_device'),
]
