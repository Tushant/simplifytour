from django.utils.html import format_html


def _base_concrete_model(abstract, klass):
    for kls in reversed(klass.__mro__):
        if issubclass(kls, abstract) and not kls._meta.abstract:
            return kls


def base_concrete_model(abstract, model):
    """
    Used in methods of abstract models to find the super-most concrete
    (non abstract) model in the inheritance chain that inherits from the
    given abstract model. This is so the methods in the abstract model can
    query data consistently across the correct concrete model.
    Consider the following::
        class Abstract(models.Model)
            class Meta:
                abstract = True
            def concrete(self):
                return base_concrete_model(Abstract, self)
        class Super(Abstract):
            pass
        class Sub(Super):
            pass
        sub = Sub.objects.create()
        sub.concrete() # returns Super
    In actual simplifytour usage, this allows methods in the ``Displayable`` and
    ``Orderable`` abstract models to access the ``Page`` instance when
    instances of custom content types, (eg: models that inherit from ``Page``)
    need to query the ``Page`` model to determine correct values for ``slug``
    and ``_order`` which are only relevant in the context of the ``Page``
    model and not the model of the custom content type.
    """
    if hasattr(model, 'objects'):
        # "model" is a model class
        return (model if model._meta.abstract else
                _base_concrete_model(abstract, model))
    # "model" is a model instance
    return (
        _base_concrete_model(abstract, model.__class__) or
        model.__class__)


def upload_to(field_path, default):
    """
    Used as the ``upload_to`` arg for file fields - allows for custom
    handlers to be implemented on a per field basis defined by the
    ``UPLOAD_TO_HANDLERS`` setting.
    """
    from django.conf import settings
    from simplifytour.utils.importing import import_dotted_path
    for k, v in settings.UPLOAD_TO_HANDLERS.items():
        if k.lower() == field_path.lower():
            return import_dotted_path(v)
    return default


class AdminThumbMixin(object):
    """
    Provides a thumbnail method on models for admin classes to
    reference in the ``list_display`` definition.
    """

    admin_thumb_field = None

    def admin_thumb(self):
        thumb = ""
        if self.admin_thumb_field:
            thumb = getattr(self, self.admin_thumb_field, "")
        if not thumb:
            return ""
        from django.conf import settings
        from simplifytour.core.templatetags.simplifytour_tags import thumbnail
        x, y = settings.ADMIN_THUMB_SIZE.split('x')
        thumb_url = thumbnail(thumb, x, y)
        return format_html("<img src='{}{}'>", settings.MEDIA_URL, thumb_url)
    admin_thumb.short_description = ""
