"""
Views for authentication and user management.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden
from apps.accounts.models import UserProfile
from apps.inventory.models import Unit

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Custom login page for NetWatch.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            error = 'Username and password are required.'
            return render(request, 'accounts/login.html', {'error': error})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f'User {username} logged in successfully')
            return redirect('dashboard:index')
        else:
            error = 'Invalid username or password.'
            logger.warning(f'Failed login attempt for username: {username}')
            return render(request, 'accounts/login.html', {'error': error, 'username': username})
    
    return render(request, 'accounts/login.html')


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """
    Logout the current user.
    """
    username = request.user.username
    logout(request)
    logger.info(f'User {username} logged out')
    return redirect('accounts:login')


def superuser_required(view_func):
    """Decorator to ensure user is a superuser."""
    def _checklogin(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('You must be a superuser to access this page.')
        return view_func(request, *args, **kwargs)
    return _checklogin


@login_required
@superuser_required
def manage_users(request):
    """List all users for superuser management."""
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'accounts/manage_users.html', context)


@login_required
@superuser_required
def add_user(request):
    """Create a new user with profile settings."""
    units = Unit.objects.all().order_by('name')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        can_manage_tokens = request.POST.get('can_manage_tokens') == 'on'
        can_create_tokens = request.POST.get('can_create_tokens') == 'on'
        view_all_locations = request.POST.get('view_all_locations') == 'on'
        allowed_units = request.POST.getlist('allowed_units')
        
        errors = {}
        
        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists.'
        
        if not password:
            errors['password'] = 'Password is required.'
        elif password != password_confirm:
            errors['password_confirm'] = 'Passwords do not match.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'
        
        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Create profile with permissions
            profile = UserProfile.objects.create(
                user=user,
                can_manage_tokens=can_manage_tokens,
                can_create_tokens=can_create_tokens,
                view_all_locations=view_all_locations,
            )
            
            # Add allowed units
            if allowed_units:
                profile.allowed_units.set(allowed_units)
            
            logger.info(f'User {username} created by {request.user.username}')
            messages.success(request, f'User "{username}" created successfully.')
            return redirect('accounts:manage_users')
        
        context = {
            'errors': errors,
            'form_data': {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'can_manage_tokens': can_manage_tokens,
                'can_create_tokens': can_create_tokens,
                'view_all_locations': view_all_locations,
            },
            'units': units,
        }
        return render(request, 'accounts/add_user.html', context)
    
    context = {'units': units}
    return render(request, 'accounts/add_user.html', context)


@login_required
@superuser_required
def edit_user(request, user_id):
    """Edit an existing user and their permissions."""
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    units = Unit.objects.all().order_by('name')
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.is_active = request.POST.get('is_active') == 'on'
        
        # Update profile permissions
        profile.can_manage_tokens = request.POST.get('can_manage_tokens') == 'on'
        profile.can_create_tokens = request.POST.get('can_create_tokens') == 'on'
        profile.view_all_locations = request.POST.get('view_all_locations') == 'on'
        
        # Update allowed units
        allowed_units = request.POST.getlist('allowed_units')
        profile.allowed_units.set(allowed_units)
        
        # Handle password change if provided
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            password_confirm = request.POST.get('password_confirm', '').strip()
            if new_password == password_confirm:
                user.set_password(new_password)
                messages.info(request, 'Password updated.')
            else:
                messages.error(request, 'Passwords do not match. Password not updated.')
        
        try:
            user.save()
            profile.save()
            logger.info(f'User {user.username} updated by {request.user.username}')
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('accounts:manage_users')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    context = {
        'user_obj': user,
        'profile': profile,
        'units': units,
        'allowed_unit_ids': profile.allowed_units.values_list('id', flat=True),
    }
    return render(request, 'accounts/edit_user.html', context)


@login_required
@superuser_required
@require_http_methods(["POST"])
def delete_user(request, user_id):
    """Delete a user."""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:manage_users')
    
    username = user.username
    user.delete()
    logger.info(f'User {username} deleted by {request.user.username}')
    messages.success(request, f'User "{username}" deleted successfully.')
    return redirect('accounts:manage_users')
