import base64
import datetime
import json
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import (
    MpesaStkPushRequestSerializer,
    MpesaPaymentSerializer,
    PaypalLogSerializer,
)
from .models import MpesaPayment, PaypalPayment
from django.utils import timezone

# ----------- Helpers: M-Pesa endpoints & tokens -----------
def get_mpesa_urls():
    if getattr(settings, "MPESA_ENV", "sandbox") == "production":
        base = "https://api.safaricom.co.ke"
    else:
        base = "https://sandbox.safaricom.co.ke"
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

# ----------- M-Pesa STK Push (real implementation) -----------
class MpesaStkPushView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Expects: { phone: "2547XXXXXXXX", amount: "100.00" }
        Initiates STK Push using Safaricom API (sandbox or production).
        """
        serializer = MpesaStkPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        amount = serializer.validated_data['amount']

        # Create local DB entry (pending)
        mpesa_obj = MpesaPayment.objects.create(phone=phone, amount=amount, status="pending")

        try:
            token = get_mpesa_token()
            urls = get_mpesa_urls()
            shortcode = settings.MPESA_SHORTCODE
            passkey = settings.MPESA_PASSKEY
            # Timestamp in format YYYYMMDDHHMMSS
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            password = generate_mpesa_password(shortcode, passkey, timestamp)

            payload = {
                "BusinessShortCode": shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(amount),
                "PartyA": phone,  # the MSISDN sending the funds
                "PartyB": shortcode,  # the shortcode receiving the funds
                "PhoneNumber": phone,
                "CallBackURL": settings.MPESA_CALLBACK_URL,
                "AccountReference": "EPICARE",
                "TransactionDesc": "Donation"
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            stk_res = requests.post(urls["stkpush"], json=payload, headers=headers, timeout=20)
            stk_res.raise_for_status()
            stk_data = stk_res.json()

            # Save the checkout_request_id & merchant_request_id if present
            mpesa_obj.mpesa_response = stk_data
            mpesa_obj.checkout_request_id = stk_data.get("CheckoutRequestID") or mpesa_obj.checkout_request_id
            mpesa_obj.merchant_request_id = stk_data.get("MerchantRequestID") or mpesa_obj.merchant_request_id
            # If response contains ResponseCode and it's 0, keep pending (STK requires callback)
            mpesa_obj.save()

            return Response({"success": True, "response": stk_data, "checkoutRequestID": mpesa_obj.checkout_request_id}, status=status.HTTP_200_OK)

        except requests.HTTPError as e:
            mpesa_obj.status = "failed"
            mpesa_obj.mpesa_response = {"error": str(e), "response_text": getattr(e.response, "text", "")}
            mpesa_obj.save()
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as exc:
            mpesa_obj.status = "failed"
            mpesa_obj.mpesa_response = {"error": str(exc)}
            mpesa_obj.save()
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------- M-Pesa Callback (Safaricom will POST here after result) -----------
class MpesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Safaricom will POST a JSON payload when STK Push result is available.
        Update MpesaPayment by checkout_request_id or merchant_request_id.
        """
        payload = request.data
        try:
            # Common sandbox payload shape: payload["Body"]["stkCallback"]
            callback = payload.get("Body", {}).get("stkCallback", payload)
            checkout_id = callback.get("CheckoutRequestID")
            result_code = callback.get("ResultCode", 1)
            merchant_id = callback.get("MerchantRequestID")

            mpesa_obj = None
            if checkout_id:
                mpesa_obj = MpesaPayment.objects.filter(checkout_request_id=checkout_id).first()
            if not mpesa_obj and merchant_id:
                mpesa_obj = MpesaPayment.objects.filter(merchant_request_id=merchant_id).first()

            if mpesa_obj:
                mpesa_obj.mpesa_response = payload
                if int(result_code) == 0:
                    mpesa_obj.status = "completed"
                else:
                    mpesa_obj.status = "failed"
                mpesa_obj.save()
            else:
                # Optional: create a log entry for unknown callbacks
                MpesaPayment.objects.create(
                    phone="unknown",
                    amount=0,
                    status="failed",
                    mpesa_response=payload,
                )

            # Respond with acknowledgment to Safaricom
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ----------- PayPal: verify webhook signature (server-side) -----------
class PaypalWebhookVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Verify incoming PayPal webhook signature using PayPal's verify-webhook-signature endpoint.
        If verified, process the event (e.g., record completed payments).
        """
        event = request.data
        # PayPal sends headers: transmission_id, transmission_time, cert_url, auth_algo, transmission_sig, webhook_id
        headers = request.headers

        # Build verification payload
        verify_payload = {
            "transmission_id": headers.get("Paypal-Transmission-Id") or headers.get("PayPal-Transmission-Id") or headers.get("paypal-transmission-id"),
            "transmission_time": headers.get("Paypal-Transmission-Time") or headers.get("paypal-transmission-time"),
            "cert_url": headers.get("Paypal-Cert-Url") or headers.get("paypal-cert-url"),
            "auth_algo": headers.get("Paypal-Auth-Algo") or headers.get("paypal-auth-algo"),
            "transmission_sig": headers.get("Paypal-Transmission-Sig") or headers.get("paypal-transmission-sig"),
            "webhook_id": getattr(settings, "PAYPAL_WEBHOOK_ID", None),  # you MUST set this to the webhook id from PayPal dev dashboard
            "webhook_event": event
        }

        # Obtain PayPal access token for webhook verification
        try:
            if getattr(settings, "PAYPAL_ENV", "sandbox") == "production":
                base = "https://api.paypal.com"
            else:
                base = "https://api.sandbox.paypal.com"

            token_res = requests.post(f"{base}/v1/oauth2/token",
                                      auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                                      data={"grant_type": "client_credentials"})
            token_res.raise_for_status()
            access_token = token_res.json().get("access_token")

            verify_res = requests.post(f"{base}/v1/notifications/verify-webhook-signature",
                                       headers={
                                           "Content-Type": "application/json",
                                           "Authorization": f"Bearer {access_token}"
                                       },
                                       json=verify_payload,
                                       timeout=15)
            verify_res.raise_for_status()
            verify_data = verify_res.json()

            # verify_data['verification_status'] should be "SUCCESS" when valid
            if verify_data.get("verification_status") == "SUCCESS":
                # Process the event (e.g., create/update PaypalPayment)
                resource = event.get("resource", {})
                order_id = resource.get("id") or resource.get("invoice_id") or resource.get("order_id")
                status_field = event.get("event_type", "UNKNOWN")
                amount = None
                currency = None
                amt_obj = resource.get("amount") or resource.get("purchase_units", [{}])[0].get("amount", {})
                if isinstance(amt_obj, dict):
                    amount = amt_obj.get("value")
                    currency = amt_obj.get("currency_code") or resource.get("currency")

                if order_id:
                    paypal_obj, created = PaypalPayment.objects.get_or_create(order_id=order_id, defaults={"amount": amount or 0, "currency": currency or "USD", "status": status_field})
                    paypal_obj.raw_payload = event
                    paypal_obj.status = status_field
                    if amount:
                        try:
                            paypal_obj.amount = amount
                        except Exception:
                            pass
                    paypal_obj.save()
                else:
                    PaypalPayment.objects.create(order_id=f"unknown-{PaypalPayment.objects.count()+1}", amount=amount or 0, currency=currency or "USD", status=status_field, raw_payload=event)

                return Response({"success": True, "verified": True}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "verified": False, "detail": verify_data}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------- PayPal: client -> server logging (paypal-log) -----------
class PaypalLogView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Accepts client-side capture details and creates/updates PaypalPayment.
        Useful if you capture on the client and want to log it on server.
        Body: { order_id, payer_id, amount, currency, raw_payload }
        """
        serializer = PaypalLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order_id = data.get("order_id")
        payer_id = data.get("payer_id")
        amount = data.get("amount")
        currency = data.get("currency") or "USD"
        raw = data.get("raw_payload") or {}

        if not order_id:
            return Response({"success": False, "error": "order_id required"}, status=status.HTTP_400_BAD_REQUEST)

        paypal_obj, created = PaypalPayment.objects.get_or_create(order_id=order_id, defaults={
            "payer_id": payer_id or "",
            "amount": amount or 0,
            "currency": currency,
            "status": "CREATED",
            "raw_payload": raw
        })

        # Update fields if provided
        if payer_id:
            paypal_obj.payer_id = payer_id
        if amount:
            paypal_obj.amount = amount
        paypal_obj.raw_payload = raw
        paypal_obj.status = "COMPLETED" if request.data.get("status") in ("COMPLETED", "PAYMENT.CAPTURE.COMPLETED") else paypal_obj.status
        paypal_obj.save()

        return Response({"success": True, "order_id": paypal_obj.order_id, "created": created}, status=status.HTTP_200_OK)
