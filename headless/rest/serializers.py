from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers

from ..registry import headless_registry
from ..settings import headless_settings
from ..utils import log


class FlexibleSerializer(FlexFieldsModelSerializer):
    """
    The flexible serializer is based on the flex fields model serializer
    and includes property fields as read-only fields.
    """

    def get_fields(self, *args, **kwargs):
        """
        Include property fields as read-only fields.
        Fields that start with "_" are excluded.
        """
        fields = super().get_fields()

        for name in dir(self.Meta.model):
            attr = getattr(self.Meta.model, name)
            if isinstance(attr, property) and name != "pk" and not name.startswith("_"):
                fields[name] = serializers.ReadOnlyField()
        return fields

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(
            field_name, model_field
        )

        return field_class, field_kwargs

    @property
    def _expandable_fields(self) -> dict:
        """
        Automatically include all related fields as expandable fields.
        """
        # Validate that Meta class exists and has model attribute
        if not hasattr(self, "Meta"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing Meta class"
            )

        if not hasattr(self.Meta, "model"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.Meta is missing model attribute"
            )

        model: Optional[Model] = self.Meta.model

        if not model:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.Meta.model is None or invalid"
            )

        # Validate that model has _meta attribute
        if not hasattr(model, "_meta"):
            raise ImproperlyConfigured(
                f"Model {model.__class__.__name__} is missing _meta attribute. "
                f"This typically indicates the model is not a proper Django model."
            )

        expandable_fields = {}

        try:
            relational_fields = [
                field for field in model._meta.get_fields() if field.is_relation
            ]
        except AttributeError as e:
            raise ImproperlyConfigured(
                f"Failed to get fields from model {model.__class__.__name__}: {str(e)}"
            ) from e

        for field in relational_fields:
            try:
                related_model = field.related_model

                # Skip if related_model is None (can happen with some field types)
                if related_model is None:
                    continue

                # Do not expand if model is not in registry
                if not headless_registry.get_model(related_model._meta.label):
                    continue

                class Serializer(headless_settings.DEFAULT_SERIALIZER_CLASS):
                    class Meta:
                        model = related_model
                        fields = "__all__"

                is_many = field.many_to_many or field.one_to_many
                name = field.name

                if is_many:
                    related_name = getattr(
                        field,
                        "related_name",
                        None,
                    )
                    accessor_name = getattr(field, "accessor_name", None)
                    name = related_name or accessor_name or field.name

                expandable_fields[name] = (
                    Serializer,
                    {"many": is_many},
                )
            except Exception as e:
                # Log the error but continue with other fields
                log.warning(
                    f"Failed to process relational field {getattr(field, 'name', 'unknown')} "
                    f"on model {model.__class__.__name__}: {str(e)}"
                )
                continue

        return expandable_fields
