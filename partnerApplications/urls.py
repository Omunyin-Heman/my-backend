from django.urls import path
from .views import PartnersCreateView

urlpatterns = [
    path('', PartnersCreateView.as_view(), name='partner-list-create'),
]
