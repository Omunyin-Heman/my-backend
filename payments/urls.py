from django.urls import path
from .views import MpesaStkPushView, MpesaCallbackView, PaypalWebhookView

from .views import (
    MpesaStkPushView,
    MpesaCallbackView,
    PaypalWebhookVerifyView,
    PaypalLogView,
)

urlpatterns = [
    path("mpesa/stkpush", MpesaStkPushView.as_view(), name="mpesa-stkpush"),
    path("mpesa/callback", MpesaCallbackView.as_view(), name="mpesa-callback"),
    path("paypal/webhook-verify", PaypalWebhookVerifyView.as_view(), name="paypal-webhook-verify"),
    path("paypal/log", PaypalLogView.as_view(), name="paypal-log"),
]
