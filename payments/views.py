import base64
import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MpesaTransactionSerializer, PaypalLogSerializer
from .models import MpesaPayment, PaypalPayment

# ----------- Helpers: M-Pesa endpoints & tokens -----------
def get_mpesa_urls():
    base = "https://api.safaricom.co.ke" if getattr(settings, "MPESA_ENV", "sandbox") == "production" else "https://sandbox.safaricom.co.ke"
    return {
        "oauth": f"{base}/oauth/v1/generate?grant_type=client_credentials",
        "stkpush": f"{base}/mpesa/stkpush/v1/processrequest",
    }

def get_mpesa_token():
    urls = get_mpesa_urls()
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    resp = requests.get(urls["oauth"], auth=(consumer_key, consumer_secret), timeout=15)
    resp.raise_for_status()
    return resp.json().get("access_token")

def generate_mpesa_password(shortcode, passkey, timestamp):
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode()

# ----------- M-Pesa STK Push -----------
class MpesaStkPushView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MpesaTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        amount = serializer.validated_data['amount']

        mpesa_obj = MpesaPayment.objects.create(phone=phone, amount=amount, status="pending")

        try:
            token = get_mpesa_token()
            urls = get_mpesa_urls()
            shortcode = settings.MPESA_SHORTCODE
            passkey = settings.MPESA_PASSKEY
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            password = generate_mpesa_password(shortcode, passkey, timestamp)

            payload = {
                "BusinessShortCode": shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(amount),
                "PartyA": phone,
                "PartyB": shortcode,
                "PhoneNumber": phone,
                "CallBackURL": settings.MPESA_CALLBACK_URL,
                "AccountReference": "EPICARE",
                "TransactionDesc": "Donation"
            }

            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            stk_res = requests.post(urls["stkpush"], json=payload, headers=headers, timeout=20)
            stk_res.raise_for_status()
            stk_data = stk_res.json()

            mpesa_obj.mpesa_response = stk_data
            mpesa_obj.checkout_request_id = stk_data.get("CheckoutRequestID")
            mpesa_obj.merchant_request_id = stk_data.get("MerchantRequestID")
            mpesa_obj.save()

            return Response({"success": True, "response": stk_data}, status=status.HTTP_200_OK)

        except Exception as e:
            mpesa_obj.status = "failed"
            mpesa_obj.mpesa_response = {"error": str(e)}
            mpesa_obj.save()
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ----------- M-Pesa Callback -----------
class MpesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.data
        try:
            callback = payload.get("Body", {}).get("stkCallback", payload)
            checkout_id = callback.get("CheckoutRequestID")
            result_code = callback.get("ResultCode", 1)
            merchant_id = callback.get("MerchantRequestID")

            mpesa_obj = MpesaPayment.objects.filter(
                checkout_request_id=checkout_id
            ).first() or MpesaPayment.objects.filter(
                merchant_request_id=merchant_id
            ).first()

            if mpesa_obj:
                mpesa_obj.mpesa_response = payload
                mpesa_obj.status = "completed" if int(result_code) == 0 else "failed"
                mpesa_obj.save()
            else:
                MpesaPayment.objects.create(phone="unknown", amount=0, status="failed", mpesa_response=payload)

            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

# ----------- PayPal Webhook Verification -----------
class PaypalWebhookVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event = request.data
        headers = request.headers
        verify_payload = {
            "transmission_id": headers.get("PayPal-Transmission-Id"),
            "transmission_time": headers.get("PayPal-Transmission-Time"),
            "cert_url": headers.get("PayPal-Cert-Url"),
            "auth_algo": headers.get("PayPal-Auth-Algo"),
            "transmission_sig": headers.get("PayPal-Transmission-Sig"),
            "webhook_id": getattr(settings, "PAYPAL_WEBHOOK_ID", None),
            "webhook_event": event,
        }

        try:
            base = "https://api.paypal.com" if getattr(settings, "PAYPAL_ENV", "sandbox") == "production" else "https://api.sandbox.paypal.com"

            token_res = requests.post(
                f"{base}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
            )
            token_res.raise_for_status()
            access_token = token_res.json().get("access_token")

            verify_res = requests.post(
                f"{base}/v1/notifications/verify-webhook-signature",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
                json=verify_payload,
                timeout=15,
            )
            verify_res.raise_for_status()
            verify_data = verify_res.json()

            if verify_data.get("verification_status") == "SUCCESS":
                PaypalPayment.objects.create(raw_payload=event, status=event.get("event_type", "UNKNOWN"))
                return Response({"success": True, "verified": True}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "verified": False, "detail": verify_data}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ----------- PayPal Log View -----------
class PaypalLogView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PaypalLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order_id = data.get("order_id")
        paypal_obj, created = PaypalPayment.objects.get_or_create(order_id=order_id, defaults=data)
        paypal_obj.raw_payload = data.get("raw_payload")
        paypal_obj.save()
        return Response({"success": True, "order_id": paypal_obj.order_id}, status=status.HTTP_200_OK)

# ----------- Payments Home (Root Endpoint) -----------
def payments_home(request):
    return JsonResponse({"message": "Payments API root — use /mpesa/ or /paypal/ endpoints"})
