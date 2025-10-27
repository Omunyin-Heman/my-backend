from django.urls import path
from .views import mpesa_stkpush, mpesa_callback, paypal_payment, create_admin

urlpatterns = [
    path('mpesa/stkpush/', mpesa_stkpush, name='mpesa_stkpush'),
    path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
    path('paypal/', paypal_payment, name='paypal_payment'),
    path('create-admin/', create_admin, name='create_admin'),
]
