from typing import Type, Dict, Any

from django.db.models import Model
from django.urls import path
from rest_framework.viewsets import ModelViewSet

from ..registry import ModelConfig, headless_registry
from ..utils import log
from .routers import rest_router, singleton_urls
from .viewsets import SingletonViewSet
from ..settings import headless_settings


class RestBuilder:
    """
    Class for building a REST API for the models in the headless
    registry.
    """

    def __init__(self):
        self._models = headless_registry.get_models()
        self._serializer_classes = {}
        self._viewset_classes = {}

    def build(self) -> None:
        """
        Builds the REST API by creating view sets and serializers and registering them
        to the router.

        Iterates through all registered models, creates appropriate viewsets and serializers,
        and registers them with the router based on whether they are singleton models
        or regular collection models.
        """
        log("\n:building_construction:  Setting up [bold]REST[/bold] routes")

        for model_config in self._models:
            # Validate model config has required fields
            if not all(
                key in model_config for key in ["model", "singleton", "search_fields"]
            ):
                log(
                    f":warning:  Invalid model config for {model_config.get('model', 'Unknown')}",
                )
                continue

            model_class = model_config["model"]
            singleton = model_config["singleton"]
            view_set = self.get_view_set(model_config)
            base_path = model_class._meta.label_lower

            if singleton:
                singleton_urls.append(
                    path(
                        base_path,
                        view_set.as_view(
                            {
                                "get": "retrieve",
                                "put": "update",
                                "patch": "partial_update",
                            }
                        ),
                    )
                )
            else:
                rest_router.register(base_path, view_set)

        log(
            f"   [cyan]•[/cyan] {len(rest_router.urls + singleton_urls)} routes registered"
        )
        log(f"     [dim]{len(singleton_urls)} singleton routes[/dim]")

    def get_serializer(self, model_class: Type[Model]) -> Type[Any]:
        """
        Get or create a serializer class for the given model.

        Args:
            model_class: The Django model class to create serializer for

        Returns:
            A serializer class for the model
        """
        model_name = model_class._meta.label

        # Return serializer class from cache if it exists
        if model_name in self._serializer_classes:
            return self._serializer_classes[model_name]

        class Serializer(headless_settings.DEFAULT_SERIALIZER_CLASS):
            class Meta:
                model = model_class
                fields = "__all__"

        self._serializer_classes[model_name] = Serializer

        return Serializer

    def get_view_set(self, model_config: ModelConfig) -> Type[Any]:
        """
        Get or create a viewset class for the given model configuration.

        Args:
            model_config: Configuration dictionary containing model and settings

        Returns:
            A viewset class configured for the model
        """
        model_class = model_config["model"]
        model_name = model_class._meta.label

        # Return cached viewset if it exists
        if model_name in self._viewset_classes:
            return self._viewset_classes[model_name]

        singleton = model_config["singleton"]
        serializer = self.get_serializer(model_class)

        if singleton:

            class ViewSet(SingletonViewSet):
                queryset = model_class.objects.none()
                serializer_class = serializer

                def get_queryset(self):
                    return model_class.objects.first()

        else:

            class ViewSet(ModelViewSet):
                queryset = model_class.objects.all()
                serializer_class = serializer
                search_fields = model_config["search_fields"]

        self._viewset_classes[model_name] = ViewSet
        return ViewSet
