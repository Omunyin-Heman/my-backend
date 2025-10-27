from django.urls import path
from .views import MpesaStkPushView, MpesaCallbackView, PaypalWebhookView, create_admin

urlpatterns = [
    path('mpesa/stkpush/', MpesaStkPushView.as_view(), name='mpesa_stkpush'),
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('paypal/webhook/', PaypalWebhookView.as_view(), name='paypal_webhook'),
    path('create-admin/', create_admin, name='create_admin'),
]
