from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('activate/<str:token>/', views.activate_account, name='activate_account'),
    path('set-password/', views.set_password_after_activation, name='set_password_after_activation'),
    path('request-activation/', views.request_activation, name='request_activation'),
]
