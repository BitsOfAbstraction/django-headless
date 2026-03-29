from decimal import Decimal, InvalidOperation

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from rest_framework.exceptions import ParseError
from rest_framework.filters import BaseFilterBackend

from ..settings import headless_settings
from ..utils import flatten


class LookupFilter(BaseFilterBackend):
    """
    A permissive filter backend that basically allows every supported lookup
    for a given field. Automatically handles multi-value lookups and booleans.
    Also supports exclusion.
    """

    MULTI_VALUE_LOOKUPS = ["in", "range"]

    TRUE_VALUES = ["true", "on", "1"]

    FALSE_VALUES = ["false", "off", "0"]

    BOOLEANS = TRUE_VALUES + FALSE_VALUES

    NONE_VALUES = ["null", "none", "empty"]

    EXCLUDE_SYMBOL = headless_settings.FILTER_EXCLUSION_SYMBOL

    NON_FILTER_FIELDS = headless_settings.NON_FILTER_FIELDS

    def filter_queryset(self, request, queryset, view):
        """
        Build the queryset based on the query params and the view's model.
        Only apply filters in list endpoints.
        """
        if getattr(view, "action", None) == "list":
            try:
                filter_kwargs, exclude_kwargs = self.get_filter_kwargs(
                    model_class=view.queryset.model,
                    query_params=request.query_params,
                )
            except Exception as e:
                raise ParseError(detail="Invalid filter parameters")
            return queryset.filter(**filter_kwargs).exclude(**exclude_kwargs).distinct()

        return queryset

    def get_filter_kwargs(self, model_class, query_params):
        filter_kwargs = {}
        exclude_kwargs = {}

        field_lookups = self.get_field_lookups(model_class=model_class)

        for key, value in query_params.lists():
            if key in self.NON_FILTER_FIELDS:
                continue
            # By default Django supports repeated multi-values (e.g. `a=1&a=2`)
            # but we allow for comma-seperated multi-values as well (e.g. `a=1,2`).
            value = flatten([param.split(",") for param in value])
            is_exclude = key.startswith(self.EXCLUDE_SYMBOL)
            # The first part of a key is considered the field name
            # Strip the exclusion symbol for field lookup
            field_name = key.split("__")[0]
            if is_exclude:
                field_name = field_name[len(self.EXCLUDE_SYMBOL) :]
            # Get the model field.
            try:
                field = model_class._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise ParseError(detail=f"Field '{field_name}' does not exist")
            # Get the allowed lookups for this field.
            lookups = field_lookups.get(field_name, [])
            try:
                # The last part of a key is considered its lookup
                # but it's not required.
                lookup = key.split("__")[-1]
                if lookup not in lookups:
                    lookup = None
            except IndexError:
                lookup = None

            # Some lookups allow multiple values, otherwise
            # the first value is used.
            is_multi = lookup in self.MULTI_VALUE_LOOKUPS
            # Depending on the field type we cast the value to
            # its correct type (i.e. number, boolean, etc.).
            if is_multi:
                casted_value = [self.cast_field_value(v, field) for v in value]
            elif lookup == "isnull":
                if not value or value not in self.BOOLEANS:
                    raise ParseError(
                        detail=f"The isnull lookup can only be used with a boolean value ({", ".join(self.BOOLEANS)})."
                    )
                casted_value = value[0] in self.TRUE_VALUES
            else:
                casted_value = self.cast_field_value(value[0], field)

            if is_exclude:
                # Strip the exclusion symbol from the key for Django's exclude method
                exclude_key = (
                    key[len(self.EXCLUDE_SYMBOL) :]
                    if key.startswith(self.EXCLUDE_SYMBOL)
                    else key
                )
                exclude_kwargs[exclude_key] = casted_value
            else:
                filter_kwargs[key] = casted_value

        return filter_kwargs, exclude_kwargs

    @staticmethod
    def get_field_lookups(model_class):
        """
        Allow all supported lookups.
        """
        field_lookups = {}
        for model_field in model_class._meta.get_fields():
            lookup_list = model_field.get_lookups().keys()
            field_lookups[model_field.name] = lookup_list
        return field_lookups

    def cast_field_value(self, value: str, field):
        value = value.strip().lower()

        if isinstance(field, models.BooleanField):
            if value in self.TRUE_VALUES:
                return True
            if value in self.FALSE_VALUES:
                return False
            if getattr(field, "null", False) and value in self.NONE_VALUES:
                return None
            else:
                if getattr(field, "null", False):
                    raise ParseError(
                        detail=f"Nullable boolean fields expect a boolean or none lookup value ({", ".join(self.BOOLEANS + self.NONE_VALUES)})."
                    )

                raise ParseError(
                    detail=f"Boolean fields expect a boolean lookup value ({", ".join(self.BOOLEANS)})."
                )

        if isinstance(field, models.IntegerField):
            try:
                return int(value)
            except ValueError:
                raise ParseError(detail=f"Invalid integer value: {value}")

        if isinstance(field, models.DecimalField):
            try:
                return Decimal(value)
            except (ValueError, InvalidOperation):
                raise ParseError(detail=f"Invalid decimal value: {value}")

        if isinstance(field, models.FloatField):
            try:
                return float(value)
            except ValueError:
                raise ParseError(detail=f"Invalid float value: {value}")

        return value
