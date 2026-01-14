from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('projects/', views.projects, name='projects'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
]