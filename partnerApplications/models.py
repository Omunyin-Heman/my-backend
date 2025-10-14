from django.db import models

class Partners(models.Model):
    organization_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    date_applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization_name
