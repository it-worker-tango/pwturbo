from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    """Login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard page (requires login)"""
    return render(request, 'accounts/dashboard.html', {
        'username': request.user.username,
        'email': request.user.email,
    })
