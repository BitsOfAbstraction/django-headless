from typing import Type, Dict, Optional, TypedDict, List

from django.db import models


class ModelConfig(TypedDict):
    model: Type[models.Model]
    singleton: bool
    search_fields: list[str]


class HeadlessRegistry:
    """
    A registry to store registered Django models.
    """

    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}

    def register(self, model_class: Type[models.Model], singleton=False, search_fields=None):
        """
        Register a model in the registry.

        Args:
            model_class: The Django model class to register
            singleton: Whether the model should be registered as a singleton
            search_fields: A list of names of text type fields on the model, such as CharField or TextField.
        """
        if not search_fields:
            search_fields = self._get_default_search_fields(model_class)

        self._models[model_class._meta.label_lower] = {
            "model": model_class,
            "singleton": singleton,
            "search_fields": [] if singleton else search_fields,
        }

    def get_model(self, label: str) -> Optional[ModelConfig]:
        """
        Get a model by label.

        Args:
            label: The label of the model to get.
        """
        return self._models.get(label.lower())

    def get_models(self) -> list[ModelConfig]:
        """
        Get all registered models.
        """
        return list(self._models.values())

    def __len__(self):
        return len(self._models)

    def _get_default_search_fields(self, model: Type[models.Model]) -> List[str]:
        """
        Returns a list of field names that are searchable (i.e. CharField).

        Args:
            model: A Django model class

        Returns:
            List of field names that are CharField or TextField instances
        """
        searchable_fields = []

        for field in model._meta.fields:
            if isinstance(field, models.CharField) and not getattr(field, "choices", None):
                searchable_fields.append(field.name)

        return searchable_fields


# Create a default registry
headless_registry = HeadlessRegistry()
