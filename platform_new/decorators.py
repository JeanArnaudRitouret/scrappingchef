from functools import wraps
import os
from django.http import HttpResponseForbidden

IS_GAE = bool(os.getenv('GAE_APPLICATION', False))

def local_environment_required(func):
    """
    Decorator that ensures the function only runs in local development environment.
    Works with both Django view functions and regular functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if IS_GAE:
            # Check if this is a view function (first arg is request)
            if args and hasattr(args[0], 'method'):
                return HttpResponseForbidden(
                    "Scraping is only available in local development environment."
                )
            else:
                # For regular functions, raise an exception
                raise RuntimeError(
                    "This function is only available in local development environment."
                )
        return func(*args, **kwargs)
    return wrapper
