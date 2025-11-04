from django.urls import path
from . import views

urlpatterns = [
    path('', views.payments_home, name='payments-home'),
    path('mpesa/stkpush/', views.MpesaStkPushView.as_view(), name='mpesa-stkpush'),
    path('mpesa/callback/', views.MpesaCallbackView.as_view(), name='mpesa-callback'),
    path('paypal/webhook/', views.PaypalWebhookVerifyView.as_view(), name='paypal-webhook'),
    path('paypal/log/', views.PaypalLogView.as_view(), name='paypal-log'),
]
