import json
import sys
from typing import List

from rich.console import Console

console = Console()


def log(*args, **kwargs):
    console.print(*args, **kwargs)


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def is_runserver():
    """
    Checks if the Django application is running as a server.

    Returns True if:
    - Django is started via WSGI/ASGI (not using manage.py)
    - Using manage.py with server commands like runserver, runserver_plus, etc.
    - Running in a context that suggests server mode (e.g., DJANGO_RUNSERVER env var)

    Returns False for management commands like migrate, makemigrations, etc.
    """
    try:
        # Check if we're using manage.py
        if sys.argv[0].endswith("/manage.py"):
            # If using manage.py, we need at least 2 arguments to have a command
            if len(sys.argv) > 1:
                # Common server commands
                server_commands = {"runserver", "runserver_plus", "runsslserver"}
                return sys.argv[1] in server_commands
            else:
                # manage.py without a command - not a server
                return False
        else:
            # If not using manage.py, assume it's a server (WSGI/ASGI)
            return True

    except IndexError:
        # If sys.argv is malformed, default to False to be safe
        return False


def flatten(xss):
    return [x for xs in xss for x in xs]


def configured_auth_classes() -> List[str] | None:
    """Return the authentication class configured in REST_FRAMEWORK"""
    from django.conf import settings

    if not hasattr(settings, "REST_FRAMEWORK"):
        return None

    auth_classes = settings.REST_FRAMEWORK.get("DEFAULT_AUTHENTICATION_CLASSES", [])

    if not auth_classes:
        return None

    auth_class_paths = []

    for auth_class in auth_classes:
        try:
            if hasattr(auth_class, "__module__") and hasattr(auth_class, "__name__"):
                full_path = auth_class.__module__ + "." + auth_class.__name__
                auth_class_paths.append(full_path)
            else:
                auth_class_paths.append(auth_class)
        except:
            pass

    return auth_classes


def is_auth_configured() -> bool:
    """Check if at least one authentication class is configured in REST_FRAMEWORK"""

    auth_classes = configured_auth_classes()

    return bool(auth_classes)


def is_secret_key_auth_configured() -> bool:
    """Check if SecretKeyAuthentication is configured"""
    from headless.settings import headless_settings

    return bool(headless_settings.AUTH_SECRET_KEY)


def is_secret_key_auth_used():
    """Check if SecretKeyAuthentication is in REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES"""
    from headless.rest.authentication import SecretKeyAuthentication

    auth_classes = configured_auth_classes()
    secret_key_class_path = (
        SecretKeyAuthentication.__module__ + "." + SecretKeyAuthentication.__name__
    )

    for auth_class in auth_classes:
        if auth_class == secret_key_class_path:
            return True

    return False
