from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Volunteer
from .serializers import VolunteerSerializer


@api_view(['GET', 'POST'])
def volunteers_view(request):
    if request.method == 'GET':
        volunteers = Volunteer.objects.all().order_by('-date_applied')
        serializer = VolunteerSerializer(volunteers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VolunteerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
