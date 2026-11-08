
from django.urls import path
from .views import (
    GuestListView,
    GuestDetailView,
    GuestCreateView,
    GuestUpdateView,
    GuestDeleteView,
    MyGuestProfileView,
)

urlpatterns = [
    path('guests/create/', GuestCreateView.as_view(), name='guest_create'),
    path('guests/', GuestListView.as_view(), name='guest_list'),
    path('guests/<int:pk>/', GuestDetailView.as_view(), name='guest_detail'),
    path('guests/<int:pk>/edit/', GuestUpdateView.as_view(), name='guest_update'),
    path('guests/<int:pk>/delete/', GuestDeleteView.as_view(), name='guest_delete'),
    path('my-guest-profile/', MyGuestProfileView.as_view(), name='my_guest_profile'),
]
