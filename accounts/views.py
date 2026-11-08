from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserChangeForm
from .forms import UserUpdateForm, ProfileUpdateForm
from django.contrib import messages
from .forms import CustomerRegistrationForm
from .models import Profile
from django.views.generic import ListView
from django.db.models import Q
from .mixins import AdminRequiredMixin
from django.views import View


@login_required
def ProfileUpdateView(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'title': "Profile Update"
    }

    return render(request, 'accounts/profile_update.html', context)


class PasswordUpdateView(LoginRequiredMixin , PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'form.html'
    success_url = reverse_lazy('profile')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Password change"
        return context
    

@login_required
def ProfileView(request):
    return render(request, 'accounts/profile.html')

def register(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                "Your account has been created. You can now log in."
            )
            return redirect("login")
    else:
        form = CustomerRegistrationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form}
    )

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.select_related('profile').order_by('-date_joined')
        q = self.request.GET.get('q', '').strip()
        role = self.request.GET.get('role', '').strip()

        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q)
            )
        if role:
            qs = qs.filter(profile__role=role)
        return qs

class UserRoleUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        new_role = request.POST.get('role')
        valid_roles = [value for value, label in Profile.ROLE_CHOICES]

        if new_role not in valid_roles:
            messages.error(request, "Invalid role.")
        elif target == request.user:
            messages.error(request, "You cannot change your own role.")
        elif target.is_superuser:
            messages.error(request, "Superuser role cannot be changed here.")
        else:
            profile, _ = Profile.objects.get_or_create(user=target)
            profile.role = new_role
            profile.save()
            messages.success(
                request,
                f"{target.username} is now {profile.get_role_display()}."
            )

        return redirect('user_list')