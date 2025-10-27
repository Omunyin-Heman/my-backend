from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import paypalrestsdk
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import base64

from .serializers import PaymentSerializer, PaypalPaymentSerializer
from .models import Payment

# ---------------------------------------------------
# 🟢 PAYPAL CONFIGURATION
# ---------------------------------------------------
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})

# ---------------------------------------------------
# 🏠 HOME ROUTE
# ---------------------------------------------------
def payment_home(request):
    return JsonResponse({
        "message": "Welcome to the Payments API 🚀",
        "available_endpoints": {
            "M-PESA STK Push": "/api/payments/mpesa/stkpush/",
            "M-PESA Callback": "/api/payments/mpesa/callback/",
            "PayPal Payment": "/api/payments/paypal/"
        }
    })


# ---------------------------------------------------
# 📲 M-PESA STK PUSH INITIATOR
# ---------------------------------------------------
@csrf_exempt
def mpesa_stkpush(request):
    try:
        data = json.loads(request.body)
        phone = data.get("phone")
        amount = data.get("amount")

        if not phone or not amount:
            return JsonResponse(
                {"success": False, "message": "Phone and amount are required"},
                status=400
            )

        # Normalize phone
        phone = str(phone).replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        # Get access token
        token_url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        token_resp = requests.get(token_url, auth=HTTPBasicAuth(
            settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return JsonResponse({"success": False, "message": "Failed to obtain access token"}, status=400)

        # Create password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        raw_pass = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(raw_pass.encode()).decode()

        # Callback URL (for live Go-Live verification)
        callback_url = getattr(settings, "MPESA_CALLBACK_URL", None) or \
            "https://my-backend-1-8oq8.onrender.com/api/payments/mpesa/callback/"

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "Epicare Donations",
            "TransactionDesc": "Donation via M-Pesa"
        }

        headers = {"Authorization": f"Bearer {access_token}"}
        stk_url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        stk_resp = requests.post(stk_url, json=payload, headers=headers)

        return JsonResponse(stk_resp.json(), status=stk_resp.status_code)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ---------------------------------------------------
# 🧾 M-PESA CALLBACK HANDLER
# ---------------------------------------------------
@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom sends a POST request here after STK transaction.
    This must return {"ResultCode":0,"ResultDesc":"Accepted"} to pass Go-Live tests.
    """
    try:
        if request.method == "POST":
            body_unicode = request.body.decode("utf-8")
            data = json.loads(body_unicode or "{}")
            print("✅ M-PESA Callback received:", json.dumps(data, indent=2))

            # Optionally: save to database
            # Payment.objects.create(provider="mpesa", data=data)

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

        return JsonResponse({"message": "M-Pesa Callback Active"})
    except Exception as e:
        print("❌ M-PESA Callback Error:", str(e))
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)})


# ---------------------------------------------------
# 💰 PAYPAL PAYMENT
# ---------------------------------------------------
@csrf_exempt
def paypal_payment(request):
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "https://epicare-frontend.vercel.app/payment-success",
                "cancel_url": "https://epicare-frontend.vercel.app/payment-cancel"
            },
            "transactions": [{
                "amount": {"total": "10.00", "currency": "USD"},
                "description": "Epicare donation or service payment"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({"approval_url": link.href})
            return JsonResponse({"error": "Approval URL not found"}, status=400)
        else:
            return JsonResponse({"error": payment.error}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
