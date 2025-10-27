from rest_framework import serializers
from .models import MpesaPayment, PaypalPayment


# ----------- M-Pesa Transaction Serializer -----------
class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaPayment
        fields = '__all__'


# ----------- PayPal Log Serializer -----------
class PaypalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaypalPayment
        fields = ['order_id', 'payer_id', 'amount', 'currency', 'raw_payload']
