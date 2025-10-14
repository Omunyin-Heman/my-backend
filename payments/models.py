from django.db import models

# Create your models here.
class MpesaPayment(models.Model):
    # STK Push initiated by server
    phone = models.CharField(max_length=13)  # e.g. 2547XXXXXXXX
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_request_id = models.CharField(max_length=255, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=32, default="pending")  # pending / completed / failed
    mpesa_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mpesa {self.phone} {self.amount} ({self.status})"


class PaypalPayment(models.Model):
    # Record created from PayPal webhook (or manual server log)
    order_id = models.CharField(max_length=255, unique=True)  # PayPal Order ID
    payer_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=64, default="pending")  # CREATED / COMPLETED / FAILED
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PayPal {self.order_id} {self.amount} ({self.status})"
