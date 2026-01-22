"""
Views for authentication.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden

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
    """Create a new user."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
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
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            
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
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            }
        }
        return render(request, 'accounts/add_user.html', context)
    
    return render(request, 'accounts/add_user.html')


@login_required
@superuser_required
def edit_user(request, user_id):
    """Edit an existing user."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username', user.username).strip()
        user.email = request.POST.get('email', '').strip()
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
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
            logger.info(f'User {user.username} updated by {request.user.username}')
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('accounts:manage_users')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    context = {'user_obj': user}
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
