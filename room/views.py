from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from .models import Room
from .forms import BookingForm
from django.urls import reverse_lazy
from main.models import Reservation
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.mixins import AdminRequiredMixin
from accounts.permissions import get_user_role

class RoomCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Room
    template_name = "form.html"
    fields = ['room_number', 'room_type', 'price_per_night', 'image']
    success_url = reverse_lazy('room_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Room"
        return context


class RoomUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Room
    template_name = "form.html"
    fields = ['room_number', 'room_type', 'price_per_night', 'image']

    def get_success_url(self):
        return reverse_lazy('room_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Room"
        return context


class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    context_object_name = "rooms"
    paginate_by = 10
    template_name = "room_list.html"

class RoomDetailView(LoginRequiredMixin, View):

    def get(self, request, pk):
        room = get_object_or_404(Room, pk=pk)

        can_see_bookings = get_user_role(request.user) in ('ADMIN', 'STAFF')

        if can_see_bookings:
            reservations = Reservation.objects.filter(
                room=room
            ).select_related('guest').order_by('check_in_date')
        else:
            reservations = Reservation.objects.none()

        context = {
            'room': room,
            'reservations': reservations,
            'can_see_bookings': can_see_bookings,
            'is_admin': get_user_role(request.user) == 'ADMIN',
        }

        return render(request, 'room_detail.html', context)