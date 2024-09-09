from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def get_handler_function():
    func_path = settings.DJ_DB_ROTATED_SECRET_FUNC

    try:
        func = import_string(func_path)
    except ImportError as e:
        raise ImproperlyConfigured(f"DJ_DB_ROTATED_SECRET_FUNC is not a valid function: {e}")

    return func
