
from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_home, name='payment_home'),
    path('mpesa/', views.mpesa_stkpush, name='mpesa_stkpush'),
    path('paypal/', views.paypal_payment, name='paypal_payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]


