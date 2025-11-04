from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Partners
from .serializers import PartnersSerializer

@api_view(['GET'])
def get_partners(request):
    partners = Partners.objects.all().order_by('-date_applied')
    serializer = PartnersSerializer(partners, many=True)
    return Response(serializer.data)
