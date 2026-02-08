from django.shortcuts import render


def home(request):
    """Home page with links to all functionality."""
    return render(request, 'inventory/home.html')
