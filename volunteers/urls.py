from django.urls import path
from . import views

urlpatterns = [
    path('', views.volunteers_view, name='volunteers_view'),
]
