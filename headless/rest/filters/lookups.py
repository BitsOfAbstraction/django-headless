def get_field_lookups(model_class):
    """
    Allow all supported lookups.

    Args:
        model_class: Django model class

    Returns:
        dict: Mapping of field names to their supported lookups
    """
    field_lookups = {}
    for model_field in model_class._meta.get_fields():
        lookup_list = model_field.get_lookups().keys()
        field_lookups[model_field.name] = lookup_list
    return field_lookups
