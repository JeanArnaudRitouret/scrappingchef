from functools import wraps
import os
from django.http import HttpResponseForbidden

IS_GAE = bool(os.getenv('GAE_APPLICATION', False))
def local_environment_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if IS_GAE:
            return HttpResponseForbidden(
                "Scraping is only available in local development environment."
            )
        return view_func(request, *args, **kwargs)
    return wrapper