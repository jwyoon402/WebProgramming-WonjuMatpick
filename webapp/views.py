"""Initial Django view. Feature-specific views are added by backend owners."""
from django.shortcuts import render


def home(request):
    return render(request, "webapp/home.html")
