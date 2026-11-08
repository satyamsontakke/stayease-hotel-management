
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (CreateView, ListView, DetailView, UpdateView, DeleteView)
from .models import Guest
from .forms import GuestProfileForm
from django.contrib import messages
from django.db.models import Q


class AdminStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user

        if user.is_superuser:
            return True

        try:
            return user.profile.role in ('ADMIN', 'STAFF')
        except user.profile.RelatedObjectDoesNotExist:
            return False


class GuestCreateView(AdminStaffRequiredMixin, CreateView):
    model = Guest
    template_name = "form.html"
    fields = [
        'first_name', 'last_name', 'email',
        'phone_number', 'government_id', 'address'
    ]
    success_url = reverse_lazy('guest_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Guest"
        return context


class GuestListView(AdminStaffRequiredMixin, ListView):
    model = Guest
    context_object_name = "guests"
    paginate_by = 10
    template_name = "guest_list.html"

    def get_queryset(self):
        queryset = Guest.objects.all().order_by('-id')
        q = self.request.GET.get('q', '').strip()

        if q:
            queryset = queryset.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(phone_number__icontains=q) |
                Q(email__icontains=q)
            )

        return queryset


class GuestDetailView(AdminStaffRequiredMixin, DetailView):
    model = Guest
    template_name = "guest_detail.html"
    context_object_name = "guest"


class GuestUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = Guest
    template_name = "form.html"
    fields = [
        'first_name', 'last_name', 'email',
        'phone_number', 'government_id', 'address'
    ]
    success_url = reverse_lazy('guest_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Guest"
        return context


class GuestDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = Guest
    template_name = "guest_confirm_delete.html"
    success_url = reverse_lazy('guest_list')

    def form_valid(self, form):
        guest = self.object

        if guest.reservation_set.exists():
            messages.error(
                self.request,
                "This guest has reservations, so it cannot be deleted. "
                "Delete or move the reservations first."
            )
            return redirect('guest_detail', pk=guest.pk)

        return super().form_valid(form)


class MyGuestProfileView(LoginRequiredMixin, UpdateView):
    model = Guest
    form_class = GuestProfileForm
    template_name = "form.html"
    success_url = reverse_lazy('reservation_create')

    def get_object(self, queryset=None):
        guest = Guest.objects.filter(user=self.request.user).first()

        if guest:
            return guest

        return Guest(
            user=self.request.user,
            email=self.request.user.email,
            first_name=self.request.user.first_name,
            last_name=self.request.user.last_name,
        )

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Guest Profile"
        return context
