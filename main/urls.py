
from django.urls import path
from . import views

from .views import (
    AvailableRoomsView,
    BookedRoomsView,
    calendar_view,
    search_rooms,
    ReservationHistoryView,
)

urlpatterns = [
    path('search-rooms/', search_rooms, name='search_rooms'),
    path('modd', views.Moddview.as_view(), name='modd'),
    path('', views.DashboardView.as_view(), name='dashboard'),

    path(
        'reservations/',
        views.ReservationListView.as_view(),
        name='reservation_list'
    ),
    path(
        'reservation/create/',
        views.ReservationCreateView.as_view(),
        name='reservation_create'
    ),
    path(
        'reservation/<int:pk>/update',
        views.ReservationUpdateView.as_view(),
        name='reservation_update'
    ),
    path(
        'reservation/<int:pk>',
        views.ReservationDetailView.as_view(),
        name='reservation_detail'
    ),
        path(
        'reservation/<int:pk>/invoice/',
        views.ReservationInvoiceView.as_view(),
        name='reservation_invoice'
    ),
        path(
        'reservation/<int:pk>/delete/',
        views.ReservationDeleteView.as_view(),
        name='reservation_delete'
    ),
    path(
        'reservation/<int:pk>/<str:action>/',
        views.ReservationStateView.as_view(),
        name='reservation_action'
    ),

    path('available-rooms/', AvailableRoomsView.as_view(), name='available_rooms'),
    path('booked-rooms/', BookedRoomsView.as_view(), name='booked_rooms'),
    path('calendar/', calendar_view, name='calendar'),
    path('reservation-history/', ReservationHistoryView.as_view(), name='reservation_history'),
]
