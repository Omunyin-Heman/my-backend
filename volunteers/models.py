from django.db import models


class Volunteer(models.Model):
    fullName = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    skills = models.TextField()
    availability = models.CharField(max_length=100)

    def __str__(self):
        return self.fullName