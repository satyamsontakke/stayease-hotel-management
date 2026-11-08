from django.db import models
from django.utils import timezone
from datetime import datetime, time

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=50)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='room_images/', blank=True, null=True)

    def is_booked_now(self):
        now = timezone.now()
        reservations = self.reservation_set.exclude(
            state__in=['CANCELLED', 'CHECKED_OUT']
        )
        return any(
            timezone.make_aware(timezone.datetime.combine(reservation.check_in_date, time(12, 0, 0)), timezone.get_current_timezone()) <= now <=
            timezone.make_aware(timezone.datetime.combine(reservation.check_out_date, time(12, 0, 0)), timezone.get_current_timezone())
            for reservation in reservations
        )
    def __str__(self):
        return self.room_number