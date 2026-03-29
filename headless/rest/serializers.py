from typing import Optional

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
        model: Optional[Model] = hasattr(self, "Meta") and self.Meta.model

        if not model:
            raise Exception("Cannot find model of default serializer.")

        expandable_fields = {}

        relational_fields = [
            field for field in model._meta.get_fields() if field.is_relation
        ]

        for field in relational_fields:
            related_model = field.related_model

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

        return expandable_fields
