from functools import wraps
from django.http.response import Http404
from django.contrib.auth.mixins import UserPassesTestMixin


def user_passes_test_or_404(test_func):
    """ Based on default 'user_passes_test'
    Decorator for views that checks that the user passes the given test,
    redirecting to 404 if not. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            raise Http404
        return _wrapped_view
    return decorator

def user_is_staff_or_404():
    """Decorator for views that checks if the user is_staff, redirecting to 404 if not."""
    return user_passes_test_or_404(lambda user: user.is_staff)

# this mixin is not used yet, therefore not tested and excluded from coverage
def user_is_superuser_or_404():
    """Decorator for views that checks if the user is_superuser, redirecting to 404 if not."""
    return user_passes_test_or_404(lambda user: user.is_superuser) # pragma: no cover - exclude from coverage

class UserPassesTest_Or404_Mixin(UserPassesTestMixin):
    """Mixin that redirects to 404 if test_func didn't pass"""
    def handle_no_permission(self):
        raise Http404

class UserIsStaff_Or404_Mixin(UserPassesTest_Or404_Mixin):
    """Mixin that checks if the user is_staff, redirecting to 404 if not."""
    def test_func(self):
        return self.request.user.is_staff

# this mixin is not used yet, therefore not tested and excluded from coverage
class UserIsSuperuser_Or404_Mixin(UserPassesTest_Or404_Mixin):
    """Mixin that checks if the user is_superuser, redirecting to 404 if not."""
    def test_func(self):
        return self.request.user.is_superuser # pragma: no cover - exclude from coverage
