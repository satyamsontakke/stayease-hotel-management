from django.contrib.auth.mixins import UserPassesTestMixin


class AdminStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user

        if user.is_superuser:
            return True

        if hasattr(user, "profile"):
            return user.profile.role in ["ADMIN", "STAFF"]

        return False

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user

        if user.is_superuser:
            return True

        if hasattr(user, "profile"):
            return user.profile.role == "ADMIN"

        return False