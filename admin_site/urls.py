from django.contrib import admin
from django.urls import path, include
from . import views
app_name = 'admin_site'
urlpatterns = [
    path('', views.user_login),
    path('home/', views.HomeView.as_view(), name='home'),
]