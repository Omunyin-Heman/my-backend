from rest_framework import serializers
from .models import MpesaPayment, PaypalPayment

class MpesaPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaPayment
        fields = "__all__"
        read_only_fields = ("checkout_request_id", "merchant_request_id", "status", "mpesa_response", "created_at", "updated_at")


class MpesaStkPushRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaypalPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaypalPayment
        fields = "__all__"
        read_only_fields = ("status","raw_payload","created_at","updated_at")
