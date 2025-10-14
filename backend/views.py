from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer
import json

# ✅ CONTACT FORM API
@api_view(['GET', 'POST'])
def contact_list_create(request):
    if request.method == 'GET':
        contacts = Contact.objects.all().order_by('-id')
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ M-PESA CALLBACK HANDLER
@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        print("✅ M-Pesa Callback Data:", data)

        # You can handle saving to DB here
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"}, status=200)

    except Exception as e:
        print("❌ Error handling M-Pesa callback:", str(e))
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Error"}, status=400)
