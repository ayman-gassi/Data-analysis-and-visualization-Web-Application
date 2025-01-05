"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('overview/', views.overview , name='overview'),
    path('logout/', views.logout, name='logout'),
    path('calculate_tool/', views.calculate_tool, name='calculate_tool'),
    path('plot_tool/', views.plot_tool, name='plot_tool'),
    path('data_analyze/', views.data_analyze, name='data_analyze'),
    path('console/', views.console, name='console'),
    path('delete_plot', views.delete_plot, name='delete_plot'),
    path('download_plot', views.download_plot, name='download_plot'),
    path('probability/', views.probability , name='probability'),
    path('probability/<str:title>/', views.probability_detail, name='probability_detail'),
    path('apply_distribution/<str:title>/', views.apply_distribution, name='apply_distribution'),
    path('delete_calcul', views.delete_calcul, name='delete_calcul'),
]
