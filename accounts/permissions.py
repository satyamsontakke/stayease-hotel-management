
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def get_user_role(user):
    if not user.is_authenticated:
        return None

    # Django superuser ko full admin access
    if user.is_superuser:
        return 'ADMIN'

    try:
        return user.profile.role
    except user.profile.RelatedObjectDoesNotExist:
        return None
    try:
        return user.profile.role
    except ObjectDoesNotExist:
        return None


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = get_user_role(request.user)

            if role not in allowed_roles:
                raise PermissionDenied(
                    'You do not have permission to access this page.'
                )

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
