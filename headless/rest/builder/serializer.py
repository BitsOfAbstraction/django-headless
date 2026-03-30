from typing import Type, Dict, Any

from django.db.models import Model

from ...settings import headless_settings


def get_serializer(model_class: Type[Model], serializer_cache: Dict[str, Type[Any]]) -> Type[Any]:
    """
    Get or create a serializer class for the given model.

    Args:
        model_class: The Django model class to create serializer for
        serializer_cache: Cache dictionary for storing created serializers

    Returns:
        A serializer class for the model
    """
    model_name = model_class._meta.label

    # Return serializer class from cache if it exists
    if model_name in serializer_cache:
        return serializer_cache[model_name]

    class Serializer(headless_settings.DEFAULT_SERIALIZER_CLASS):
        class Meta:
            model = model_class
            fields = "__all__"

    serializer_cache[model_name] = Serializer

    return Serializer
