from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy
from .models import Reservation
from django.views.generic import DetailView
from django import forms
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from room.models import Room
from guest.models import Guest
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.utils.dateparse import parse_date
from accounts.mixins import AdminStaffRequiredMixin
from accounts.permissions import get_user_role, role_required


class CustomReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'guest', 'check_in_date', 'check_out_date', 'additional']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].label_from_instance = lambda room: (
            f"Room {room.room_number} - {room.room_type} - "
            f"Rs {room.price_per_night}/night"
        )


class Moddview(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'modd.html')


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        today = now().date()
        is_manager = get_user_role(request.user) in ('ADMIN', 'STAFF')

        total_rooms = Room.objects.count()

        booked_rooms = Reservation.objects.blocking().filter(
            check_in_date__lte=today,
            check_out_date__gt=today
        ).values('room').distinct().count()

        available_rooms = total_rooms - booked_rooms

        if total_rooms:
            occupancy = round(booked_rooms * 100 / total_rooms)
        else:
            occupancy = 0

        context = {
            'today': today,
            'is_manager': is_manager,
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'booked_rooms': booked_rooms,
            'occupancy': occupancy,
        }

        if is_manager:
            context['total_guests'] = Guest.objects.count()
            context['total_reservations'] = Reservation.objects.count()
            context['checkins'] = Reservation.objects.blocking().filter(
                check_in_date=today
            ).select_related('room', 'guest')
            context['checkouts'] = Reservation.objects.blocking().filter(
                check_out_date=today
            ).select_related('room', 'guest')
        else:
            context['my_next'] = Reservation.objects.blocking().filter(
                guest__user=request.user,
                check_out_date__gt=today
            ).select_related('room').order_by('check_in_date').first()

        return render(request, 'dashboard.html', context)


class AvailableRoomsView(LoginRequiredMixin, View):
    def get(self, request):
        today = now().date()

        booked_room_ids = Reservation.objects.blocking().filter(
            check_in_date__lte=today,
            check_out_date__gt=today
        ).values_list('room_id', flat=True)

        available_rooms = Room.objects.exclude(id__in=booked_room_ids)

        return render(request, 'available_rooms.html', {
            'rooms': available_rooms
        })


class BookedRoomsView(AdminStaffRequiredMixin, View):
    def get(self, request):
        today = now().date()

        booked_rooms = Reservation.objects.blocking().filter(
            check_in_date__lte=today,
            check_out_date__gt=today
        ).select_related('room', 'guest')

        return render(request, 'booked_rooms.html', {
            'reservations': booked_rooms
        })


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    template_name = "form.html"
    form_class = CustomReservationForm

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.is_authenticated:
            if user.is_superuser:
                return super().dispatch(request, *args, **kwargs)

            try:
                role = user.profile.role
            except Exception:
                raise PermissionDenied("Profile is not configured.")

            if role not in ('ADMIN', 'STAFF', 'CUSTOMER'):
                raise PermissionDenied("Access denied.")

            if role == 'CUSTOMER':
                if not Guest.objects.filter(user=user).exists():
                    return redirect('my_guest_profile')

        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        user = self.request.user
        if not user.is_superuser:
            try:
                role = user.profile.role
            except Exception:
                role = None

            if role == 'CUSTOMER':
                form.fields.pop('guest', None)

        return form

    def get_initial(self):
        initial = super().get_initial()
        guest_id = self.request.GET.get('guest_id')
        room_id = self.request.GET.get('room_id')

        if guest_id and get_user_role(self.request.user) in ('ADMIN', 'STAFF'):
            initial['guest'] = guest_id

        if room_id:
            initial['room'] = room_id

        for key in ('check_in_date', 'check_out_date'):
            value = self.request.GET.get(key)
            if value:
                initial[key] = value

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Reservation"
        return context

    def form_valid(self, form):
        user = self.request.user

        if not user.is_superuser:
            try:
                role = user.profile.role
            except Exception:
                role = None

            if role == 'CUSTOMER':
                guest = Guest.objects.filter(user=user).first()

                if not guest:
                    return redirect('my_guest_profile')

                form.instance.guest = guest

        room = form.cleaned_data['room']
        check_in_date = form.cleaned_data['check_in_date']
        check_out_date = form.cleaned_data['check_out_date']

        if check_out_date <= check_in_date:
            form.add_error(
                'check_out_date',
                'Check-out date must be after check-in date.'
            )
            return self.form_invalid(form)

        existing_reservations = Reservation.objects.blocking().filter(
            room=room,
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        )

        if existing_reservations.exists():
            form.add_error(
                'room',
                'This room is already booked for the selected dates.'
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    template_name = "form.html"
    form_class = CustomReservationForm

    def get_queryset(self):
        queryset = self._allowed().exclude(state__in=['CANCELLED', 'CHECKED_OUT'])

        if get_user_role(self.request.user) == 'CUSTOMER':
            queryset = queryset.filter(state='CONFIRMED')

        return queryset

    def _allowed(self):
        user = self.request.user

        if user.is_superuser:
            return Reservation.objects.all()

        try:
            role = user.profile.role
        except Exception:
            raise PermissionDenied("Profile is not configured.")

        if role in ('ADMIN', 'STAFF'):
            return Reservation.objects.all()

        if role == 'CUSTOMER':
            return Reservation.objects.filter(guest__user=user)

        raise PermissionDenied("Access denied.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        if not user.is_superuser:
            try:
                role = user.profile.role
            except Exception:
                role = None

            if role == 'CUSTOMER':
                form.fields.pop('guest', None)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Reservation"
        return context

    def form_valid(self, form):
        room = form.cleaned_data['room']
        check_in_date = form.cleaned_data['check_in_date']
        check_out_date = form.cleaned_data['check_out_date']

        if check_out_date <= check_in_date:
            form.add_error(
                'check_out_date',
                'Check-out date must be after check-in date.'
            )
            return self.form_invalid(form)

        existing_reservations = Reservation.objects.blocking().filter(
            room=room,
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        ).exclude(pk=self.object.pk)

        if existing_reservations.exists():
            form.add_error(
                'room',
                'This room is already booked for the selected dates.'
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservation_detail.html"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Reservation.objects.all()

        try:
            role = user.profile.role
        except Exception:
            raise PermissionDenied("Profile is not configured.")

        if role in ('ADMIN', 'STAFF'):
            return Reservation.objects.all()

        if role == 'CUSTOMER':
            return Reservation.objects.filter(guest__user=user)

        raise PermissionDenied("Access denied.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = self.object
        role = get_user_role(self.request.user)
        is_manager = role in ('ADMIN', 'STAFF')
        today = now().date()

        context['is_admin'] = role == 'ADMIN'
        context['can_checkin'] = (
            is_manager and reservation.state == 'CONFIRMED'
            and today >= reservation.check_in_date
        )
        context['can_checkout'] = is_manager and reservation.state == 'CHECKED_IN'
        context['can_cancel'] = reservation.state == 'CONFIRMED' and (
            is_manager or today < reservation.check_in_date
        )
        context['can_edit'] = (
            reservation.state == 'CONFIRMED'
            or (is_manager and reservation.state == 'CHECKED_IN')
        )

        return context

class ReservationInvoiceView(ReservationDetailView):
    template_name = "invoice.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.state == 'CANCELLED':
            messages.error(request, "There is no invoice for a cancelled booking.")
            return redirect('reservation_detail', pk=self.object.pk)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issued'] = now().date()
        
        return context
    
class ReservationStateView(LoginRequiredMixin, View):
    """Check-in, check-out and cancel (POST only)."""

    def post(self, request, pk, action):
        reservation = get_object_or_404(Reservation, pk=pk)
        role = get_user_role(request.user)
        is_manager = role in ('ADMIN', 'STAFF')
        today = now().date()

        if not is_manager:
            owns_it = (
                role == 'CUSTOMER'
                and reservation.guest.user_id == request.user.id
            )
            if not owns_it or action != 'cancel':
                raise PermissionDenied("Access denied.")

        if action == 'checkin':
            if reservation.state != 'CONFIRMED':
                messages.error(request, "Only a confirmed booking can be checked in.")
            elif today < reservation.check_in_date:
                messages.error(request, "The check-in date has not arrived yet.")
            else:
                reservation.state = 'CHECKED_IN'
                reservation.save(update_fields=['state'])
                messages.success(request, "Guest checked in.")

        elif action == 'checkout':
            if reservation.state != 'CHECKED_IN':
                messages.error(request, "Only a checked-in guest can be checked out.")
            else:
                reservation.state = 'CHECKED_OUT'
                reservation.save(update_fields=['state'])
                messages.success(request, "Guest checked out.")

        elif action == 'cancel':
            if reservation.state != 'CONFIRMED':
                messages.error(request, "This booking can no longer be cancelled.")
            elif not is_manager and today >= reservation.check_in_date:
                messages.error(request, "Booking has already started. Please contact the hotel.")
            else:
                reservation.state = 'CANCELLED'
                reservation.save(update_fields=['state'])
                messages.success(request, "Booking cancelled.")

        else:
            raise PermissionDenied("Unknown action.")

        return redirect('reservation_detail', pk=reservation.pk)


class AdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return get_user_role(self.request.user) == 'ADMIN'


class ReservationDeleteView(AdminOnlyMixin, DeleteView):
    model = Reservation
    template_name = "reservation_confirm_delete.html"
    success_url = reverse_lazy('reservation_list')

    def form_valid(self, form):
        messages.success(self.request, "Reservation deleted.")
        return super().form_valid(form)


class ReservationListView(LoginRequiredMixin, ListView):
    show_history = False
    model = Reservation
    paginate_by = 10
    context_object_name = "reservations"
    template_name = "reservation_list.html"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            queryset = Reservation.objects.all()
        else:
            try:
                role = user.profile.role
            except Exception:
                raise PermissionDenied("Profile is not configured.")

            if role in ('ADMIN', 'STAFF'):
                queryset = Reservation.objects.all()
            elif role == 'CUSTOMER':
                queryset = Reservation.objects.filter(guest__user=user)
            else:
                raise PermissionDenied("Access denied.")

        room_number = self.request.GET.get('room_number')

        if room_number:
            queryset = queryset.filter(room__room_number=room_number)

        today = now().date()

        active = (
            Q(state='CHECKED_IN') |
            Q(state='CONFIRMED', check_out_date__gt=today)
        )

        if getattr(self, 'show_history', False):
            queryset = queryset.exclude(active)
        else:
            queryset = queryset.filter(active)

        queryset = queryset.select_related('room', 'guest')

        return queryset.order_by('-id')


class ReservationHistoryView(ReservationListView):
    show_history = True


@role_required('ADMIN', 'STAFF')
def calendar_view(request):
    today = now().date()
    span = 14

    start = parse_date(request.GET.get('start') or '') or today
    days = [start + timedelta(days=i) for i in range(span)]
    end = start + timedelta(days=span)

    reservations = Reservation.objects.blocking().filter(
        check_in_date__lt=end,
        check_out_date__gt=start
    ).select_related('guest')

    # (room_id, date) -> reservation
    booked = {}
    for reservation in reservations:
        day = max(reservation.check_in_date, start)
        last = min(reservation.check_out_date, end)
        while day < last:
            booked[(reservation.room_id, day)] = reservation
            day += timedelta(days=1)

    rows = []
    for room in Room.objects.all().order_by('room_number'):
        rows.append({
            'room': room,
            'cells': [
                {'date': day, 'booking': booked.get((room.id, day))}
                for day in days
            ],
        })

    return render(request, 'calendar.html', {
        'days': days,
        'rows': rows,
        'today': today,
        'start': start,
        'last_day': end - timedelta(days=1),
        'prev_start': start - timedelta(days=span),
        'next_start': end,
    })


@login_required
def search_rooms(request):
    check_in = parse_date(request.GET.get('check_in') or '')
    check_out = parse_date(request.GET.get('check_out') or '')

    available_rooms = []

    if check_in and check_out and check_out > check_in:
        booked_room_ids = Reservation.objects.blocking().filter(
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        ).values_list('room_id', flat=True)

        available_rooms = Room.objects.exclude(id__in=booked_room_ids)

    return render(request, 'search_rooms.html', {
        'rooms': available_rooms,
        'check_in': request.GET.get('check_in'),
        'check_out': request.GET.get('check_out')
    })