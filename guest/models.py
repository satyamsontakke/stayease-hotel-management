
from django.db import models
from django.contrib.auth.models import User


class Guest(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guest_profile'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    government_id = models.CharField(max_length=15)
    address = models.TextField(max_length=200)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.phone_number}"
