from rest_framework import generics
from .models import Partners
from .serializers import PartnersSerializer

class PartnersCreateView(generics.ListCreateAPIView):
    queryset = Partners.objects.all().order_by('-date_applied')
    serializer_class = PartnersSerializer
