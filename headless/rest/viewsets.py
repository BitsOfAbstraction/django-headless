from rest_framework.exceptions import NotFound
from rest_framework.mixins import (
    CreateModelMixin,
    UpdateModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet


class SingletonViewSet(
    GenericViewSet,
    CreateModelMixin,
    UpdateModelMixin,
    RetrieveModelMixin,
):
    """
    A model view set for singleton objects.
    """

    def update(self, request, *args, **kwargs):
        """
        If a singleton doesn't exist, it will be created.
        """
        try:
            return super().update(request, *args, **kwargs)
        except NotFound:
            return self.create(request, *args, **kwargs)

    def get_object(self):
        """
        Get the first object of the queryset (assuming there is only one object).
        If a singleton doesn't exist, it will raise a NotFound exception.
        """
        obj = self.get_queryset()

        if not obj:
            raise NotFound()

        self.check_object_permissions(self.request, obj)

        return obj
