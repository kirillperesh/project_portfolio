from functools import wraps
from django.http.response import Http404


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
    """Decorator for views that checks that the user is_staff,redirecting to 404 if not."""
    return user_passes_test_or_404(lambda user: user.is_staff)
