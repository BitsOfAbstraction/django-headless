__title__ = "Django Headless"
__version__ = "1.0.0-beta.6"
__author__ = "Leon van der Grient"
__license__ = "MIT"

from typing import Type

from django.db import models
from .registry import headless_registry

# Version synonym
VERSION = __version__


def expose(singleton=False, search_fields=None):
    """
    Decorator to register a Django model to the headless registry.

    Usage:
        @expose()
        class MyModel(models.Model):
            pass
    """

    def decorator(model_class: Type[models.Model]):
        expose_model(model_class, singleton=singleton, search_fields=search_fields)

        return model_class

    return decorator


def expose_model(model_class: Type[models.Model], singleton=False, search_fields=None):
    headless_registry.register(
        model_class, singleton=singleton, search_fields=search_fields
    )
