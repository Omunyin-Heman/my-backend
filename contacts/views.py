from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer


@api_view(['GET', 'POST'])
def contact_list_create(request):
    """
    Handles both GET and POST for Contacts
    """
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

# ✅ New endpoint to update status (Read/Unread)
@api_view(['PATCH'])
def contact_update_status(request, pk):
    try:
        contact = Contact.objects.get(pk=pk)
    except Contact.DoesNotExist:
        return Response({"error": "Contact not found"}, status=404)

    new_status = request.data.get("status")
    if new_status not in ["Read", "Unread"]:
        return Response({"error": "Invalid status value"}, status=400)

    contact.status = new_status
    contact.save()
    return Response({"message": f"Status updated to {new_status}"}, status=200)
