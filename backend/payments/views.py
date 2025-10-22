import paypalrestsdk
import requests
import base64
from requests.auth import HTTPBasicAuth
from datetime import datetime
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json


# ========== PAYPAL CONFIGURATION ==========
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # 'sandbox' or 'live'
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})


# ========== HOME ROUTE ==========
def payment_home(request):
    return JsonResponse({"message": "Welcome to the Payments API"})


# ========== M-PESA STK PUSH PAYMENT ==========
@csrf_exempt
def mpesa_stkpush(request):
    """Initiate M-Pesa STK Push (Daraja Sandbox)"""
    try:
        data = json.loads(request.body)
        phone = data.get("phone")
        amount = data.get("amount")

        if not phone or not amount:
            return JsonResponse({
                "success": False,
                "message": "Phone number and amount are required"
            }, status=400)

        # ✅ Format phone number correctly
        phone = str(phone).replace(" ", "").replace("+", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        # ✅ STEP 1: Get Access Token
        token_url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        token_response = requests.get(
            token_url,
            auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )

        print("🔹 Access Token Status:", token_response.status_code)
        print("🔹 Access Token Text:", token_response.text)

        # Validate token response
        try:
            token_data = token_response.json()
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "Invalid token response (not JSON)",
                "raw_response": token_response.text
            }, status=400)

        access_token = token_data.get("access_token")
        if not access_token:
            return JsonResponse({
                "success": False,
                "message": "Failed to obtain access token",
                "token_response": token_data
            }, status=400)

        # ✅ STEP 2: Generate Password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        raw_password = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        encoded_password = base64.b64encode(raw_password.encode()).decode()

        # ✅ STEP 3: Use callback URL from environment
        callback_url = getattr(settings, "MPESA_CALLBACK_URL", None)
        if not callback_url:
            return JsonResponse({
                "success": False,
                "message": "Callback URL not configured in environment"
            }, status=500)

        # ✅ STEP 4: Prepare STK Push Payload
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": encoded_password,
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

        stk_response = requests.post(stk_url, json=payload, headers=headers)

        print("🔹 STK Push Status:", stk_response.status_code)
        print("🔹 STK Push Text:", stk_response.text)

        try:
            return JsonResponse(stk_response.json())
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "STK Push returned non-JSON response",
                "raw_response": stk_response.text
            }, status=400)

    except Exception as e:
        print("❌ M-Pesa Error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ========== PAYPAL PAYMENT ==========
@csrf_exempt
def paypal_payment(request):
    """Create PayPal sandbox payment"""
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


# ========== M-PESA CALLBACK ==========
@csrf_exempt
def mpesa_callback(request):
    """Handle callback from M-Pesa (for logging or database saving)"""
    try:
        body_unicode = request.body.decode('utf-8')
        if not body_unicode.strip():
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Empty request body"})

        data = json.loads(body_unicode)
        print("📥 M-Pesa Callback received:", json.dumps(data, indent=4))

        # You can save data in DB here later
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    except json.JSONDecodeError:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON format"})
    except Exception as e:
        print("❌ Callback Error:", e)
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)})
