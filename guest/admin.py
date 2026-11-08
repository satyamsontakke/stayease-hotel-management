
from django.contrib import admin
from .models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'user',
    )
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('user',)
