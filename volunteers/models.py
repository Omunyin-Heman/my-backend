from django.db import models
from django.utils import timezone

class Volunteer(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    skills = models.TextField()
    availability = models.BooleanField(default=False)
    date_applied = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.full_name
