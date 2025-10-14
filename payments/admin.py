from django.contrib import admin
from .models import MpesaPayment, PaypalPayment
# Register your models here.
@admin.register(MpesaPayment)
class MpesaPaymentAdmin(admin.ModelAdmin):
    list_display = ("phone", "amount", "status", "checkout_request_id", "created_at")
    search_fields = ("phone", "checkout_request_id", "merchant_request_id")
    readonly_fields = ("created_at","updated_at")

@admin.register(PaypalPayment)
class PaypalPaymentAdmin(admin.ModelAdmin):
    list_display = ("order_id", "amount", "currency", "status", "created_at")
    search_fields = ("order_id",)
    readonly_fields = ("created_at","updated_at")
