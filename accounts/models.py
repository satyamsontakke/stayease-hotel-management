
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('CUSTOMER', 'Customer'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    email = models.EmailField()
    photo = models.ImageField(
        upload_to='profile_photos/',
        default='default.png'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='CUSTOMER'
    )

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'email': instance.email or ''}
        )


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    profile, created = Profile.objects.get_or_create(
        user=instance,
        defaults={'email': instance.email or ''}
    )
    if not created:
        profile.save()
