from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect


def login_view(request):

    if request.method == 'POST':        
        
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('search:index')
        else:
            return HttpResponse(f'Invalid credentials')

    return render(request, 'account/pages-login.html')

@login_required
def user_profile(request):
    return render(request, 'account/users-profile.html')

@login_required
def user_register(request):
    return render(request, 'account/pages-register.html')