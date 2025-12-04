from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

# Create your views here.
def landing(request):
    return render(request, 'accounts/landing.html')
