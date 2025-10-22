from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Welcome to Epicare Backend API 🚀",
        "endpoints": {
            "Admin": "/admin/",
            "Partner Applications API": "/api/partners/",
            "Volunteer Applications API": "/api/volunteers/",
            "Payments API": "/api/payments/",
        }
    })

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/payments/', include('payments.urls')),  # ✅ include payments app
    path('api/partners/', include('partnerApplications.urls')),
    path('api/volunteers/', include('volunteers.urls')),
    path('api/contacts/', include('contacts.urls')),
]
