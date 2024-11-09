from django.urls import path
from . import views

# define the URL patterns for the app
urlpatterns = [
    path('', views.index, name='index'),
]