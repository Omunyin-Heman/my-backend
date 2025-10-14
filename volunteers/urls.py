from django.urls import path
from . import views

urlpatterns = [
    path('', views.volunteer_list, name='volunteer-list'),
]
