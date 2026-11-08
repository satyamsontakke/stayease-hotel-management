from django.urls import path
from . import views

urlpatterns = [
    path("password_update/", views.PasswordUpdateView.as_view(), name='password-update'),
    path("profile/", views.ProfileView, name='profile'),
    path("profile/update/", views.ProfileUpdateView, name='profile-update'),
    path("register/", views.register, name="register"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/role/", views.UserRoleUpdateView.as_view(), name="user_role_update"),
]