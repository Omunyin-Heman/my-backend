from django.urls import path
from . import views

urlpatterns = [
    path('', views.PartnersCreateView.as_view(), name='partner-list-create'),
]
