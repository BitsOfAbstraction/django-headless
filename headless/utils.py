import json
import sys

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
