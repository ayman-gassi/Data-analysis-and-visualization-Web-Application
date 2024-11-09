from django.shortcuts import redirect, render
from .forms import ContactForm

# Create your views here.
def index(request):
    return render(request, 'index.html')
