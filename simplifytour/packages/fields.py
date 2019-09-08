from __future__ import unicode_literals

from django.conf import settings

from simplifytour.core.fields import MultiChoiceField


class MenusField(MultiChoiceField):
    """
    ``MultiChoiceField`` for specifying which menus a package should
    appear in.
    """

    def __init__(self, *args, **kwargs):
        choices = [t[:2] for t in getattr(settings, "PAGE_MENU_TEMPLATES", [])]
        default = getattr(settings, "PAGE_MENU_TEMPLATES_DEFAULT", None)
        if default is None:
            default = [t[0] for t in choices]
        elif not default:
            default = None
        if isinstance(default, (tuple, list)):
            d = tuple(default)
            default = self.get_default_value(d)
        defaults = {"max_length": 100, "choices": choices, "default": default}
        defaults.update(kwargs)
        super(MenusField, self).__init__(*args, **defaults)

    @staticmethod
    def get_default_value(d):
        return d