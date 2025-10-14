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
            return JsonResponse({"success": False, "message": "Phone and amount are required"}, status=400)

        # Clean phone format
        phone = str(phone).replace(" ", "").replace("+", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        # STEP 1: Get Access Token
        token_url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(token_url, auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))

        print("🔹 Access Token Response Status:", response.status_code)
        print("🔹 Access Token Response Text:", response.text)

        # ✅ Handle empty or non-JSON token response
        try:
            token_data = response.json()
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "Invalid token response (not JSON)",
                "raw_response": response.text
            }, status=400)

        access_token = token_data.get("access_token")
        if not access_token:
            return JsonResponse({
                "success": False,
                "message": "Failed to get access token",
                "token_response": token_data
            }, status=400)

        # STEP 2: Generate Password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        raw_password = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        encoded_password = base64.b64encode(raw_password.encode()).decode()

        # STEP 3: Prepare STK Push Payload
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": encoded_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": "https://2f3a-102-134-50-23.ngrok-free.app/api/payments/mpesa/callback/",
            "AccountReference": "Epicare Donations",
            "TransactionDesc": "Donation via M-Pesa"
        }

        headers = {"Authorization": f"Bearer {access_token}"}
        stk_url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        stk_response = requests.post(stk_url, json=payload, headers=headers)

        print("🔹 STK Push Response Status:", stk_response.status_code)
        print("🔹 STK Push Response Text:", stk_response.text)

        try:
            return JsonResponse(stk_response.json())
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "STK Push returned non-JSON response",
                "raw_response": stk_response.text
            }, status=400)

    except Exception as e:
        print("❌ M-Pesa error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)



# ========== PAYPAL PAYMENT ==========
@csrf_exempt
def paypal_payment(request):
    """Create PayPal sandbox payment"""
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:3000/payment-success",
            "cancel_url": "http://localhost:3000/payment-cancel"
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

@csrf_exempt
def mpesa_callback(request):
    """Handle callback from M-Pesa (for logging or database saving)"""
    try:
        # Ensure body is not empty and parse JSON
        body_unicode = request.body.decode('utf-8')
        if not body_unicode.strip():
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Empty request body"})

        data = json.loads(body_unicode)

        print("📥 M-Pesa Callback received:", json.dumps(data, indent=4))

        # You can later store it in DB here
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    except json.JSONDecodeError:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON format"})
    except Exception as e:
        print("Callback error:", e)
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)})
