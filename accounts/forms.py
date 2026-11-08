from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo']


from django.contrib.auth.forms import UserCreationForm


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
