from django.urls import path
from . import views

urlpatterns = [
    path('', views.contact_list_create, name='contact-list-create'),
    path('<int:pk>/status/', views.contact_update_status, name='contact-update-status'),
]
