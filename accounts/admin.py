

from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'email')
