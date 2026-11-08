from django.db import models
from django.urls import reverse
from django.utils import timezone


class ReservationQuerySet(models.QuerySet):
    def blocking(self):
        """Reservations that still occupy a room (not cancelled / checked-out)."""
        return self.exclude(state__in=['CANCELLED', 'CHECKED_OUT'])


class Reservation(models.Model):
    STATE_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked-in'),
        ('CHECKED_OUT', 'Checked-out'),
        ('CANCELLED', 'Cancelled'),
    ]

    room = models.ForeignKey('room.Room', on_delete=models.CASCADE)
    guest = models.ForeignKey('guest.Guest', on_delete=models.CASCADE)
    additional = models.TextField(null=True,blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    state = models.CharField(
        max_length=12,
        choices=STATE_CHOICES,
        default='CONFIRMED',
    )

    objects = ReservationQuerySet.as_manager()

    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days

    @property
    def total_price(self):
        return self.nights * self.room.price_per_night

    @property
    def status(self):
        if self.state == 'CANCELLED':
            return 'Cancelled'
        if self.state == 'CHECKED_OUT':
            return 'Checked-out'
        if self.state == 'CHECKED_IN':
            return 'Checked-in'

        if timezone.localdate() < self.check_in_date:
            return 'Upcoming'
        return 'Confirmed'

    def get_absolute_url(self):
        return reverse('reservation_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.room.room_number} | form {self.check_in_date} to {self.check_out_date}"