from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from partnerApplications.models import Partners
from volunteers.models import Volunteer
from contacts.models import Contact  # ✅ make sure this matches your actual model name


# Home route
def home(request):
    return JsonResponse({
        "message": "Welcome to Epicare Backend API 🚀",
        "endpoints": {
            "Admin": "/admin/",
            "Partner Applications API": "/api/partners/",
            "Volunteer Applications API": "/api/volunteers/",
            "Payments API": "/api/payments/",
            "Dashboard Counts": "/api/dashboard-counts/",
        }
    })


# ✅ Fixed dashboard counts
def dashboard_counts(request):
    data = {
        "partners": Partners.objects.count(),
        "volunteers": Volunteer.objects.count(),
        "contacts": Contact.objects.count(),  # ✅ change this to your contact model name
    }
    return JsonResponse(data)


urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),

    # API routes
    path('api/payments/', include('payments.urls')),
    path('api/partners/', include('partnerApplications.urls')),
    path('api/volunteers/', include('volunteers.urls')),
    path('api/contacts/', include('contacts.urls')),

    # ✅ Dashboard counts endpoint
    path('api/dashboard-counts/', dashboard_counts),
]
