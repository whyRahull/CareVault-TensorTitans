from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def org_admin_required(function=None, login_url='/login/'):
    """
    Decorator for views that checks that the user is logged in, has 'org_admin' role,
    and belongs to an organisation.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.role == 'admin' or u.is_superuser) and u.organisation is not None,
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
