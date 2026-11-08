
from django import forms
from .models import Guest


class GuestProfileForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'government_id',
            'address',
        ]

        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
