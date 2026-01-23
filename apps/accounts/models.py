"""
User profile and permission models for NetWatch.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.inventory.models import Unit


class UserProfile(models.Model):
    """
    Extended user profile with NetWatch-specific settings.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='netwatch_profile'
    )
    
    # Permissions
    can_manage_tokens = models.BooleanField(
        default=False,
        help_text="Can create/delete API tokens"
    )
    can_create_tokens = models.BooleanField(
        default=False,
        help_text="Can create new API tokens"
    )
    
    # Country/Location visibility
    view_all_locations = models.BooleanField(
        default=False,
        help_text="Can see devices from all locations/countries"
    )
    
    allowed_locations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of location strings user can see (empty if view_all_locations=True)"
    )
    
    allowed_units = models.ManyToManyField(
        Unit,
        blank=True,
        related_name='authorized_users',
        help_text="Units/brands this user can see devices from"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_allowed_locations(self) -> list:
        """Return list of allowed location strings."""
        if self.view_all_locations:
            return []  # Empty list means all locations
        return self.allowed_locations or []

    def get_allowed_units(self):
        """Return queryset of allowed units."""
        return self.allowed_units.all()

    def can_view_device(self, device) -> bool:
        """Check if user can view a specific device."""
        if self.view_all_locations:
            return True
        
        # Check location
        if device.location and device.location in self.allowed_locations:
            return True
        
        # Check unit
        if device.unit and self.allowed_units.filter(id=device.unit.id).exists():
            return True
        
        return False
