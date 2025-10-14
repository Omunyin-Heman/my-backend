from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Volunteer
from .serializers import VolunteerSerializer

@api_view(['GET', 'POST'])
def volunteer_list(request):
    if request.method == 'GET':
        volunteers = Volunteer.objects.all()
        serializer = VolunteerSerializer(volunteers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VolunteerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
