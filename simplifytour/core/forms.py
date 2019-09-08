from django.utils.safestring import mark_safe
from django.conf import settings
from django import forms

from simplifytour.utils.static import static_lazy as static


class OrderWidget(forms.HiddenInput):
    """
    Add up and down arrows for ordering controls next to a hidden
    form field.
    """

    @property
    def is_hidden(self):
        return False

    def render(self, *args, **kwargs):
        rendered = super(OrderWidget, self).render(*args, **kwargs)
        arrows = ["<img src='%sadmin/img/admin/arrow-%s.gif' />" %
            (settings.STATIC_URL, arrow) for arrow in ("up", "down")]
        arrows = "<span class='ordering'>%s</span>" % "".join(arrows)
        return rendered + mark_safe(arrows)


class TinyMceWidget(forms.Textarea):
    """
    Setup the JS files and targetting CSS class for a textarea to
    use TinyMCE.
    """

    class Media:
        js = [static("simplifytour/tinymce/tinymce.min.js"),
              static("simplifytour/tinymce/jquery.tinymce.min.js"),
              static(settings.TINYMCE_SETUP_JS)]
        css = {'all': [static("simplifytour/tinymce/tinymce.css")]}

    def __init__(self, *args, **kwargs):
        super(TinyMceWidget, self).__init__(*args, **kwargs)
        self.attrs["class"] = "mceEditor"


class DynamicInlineAdminForm(forms.ModelForm):
    """
    Form for ``DynamicInlineAdmin`` that can be collapsed and sorted
    with drag and drop using ``OrderWidget``.
    """

    class Media:
        js = [static("simplifytour/js/%s" % settings.JQUERY_UI_FILENAME),
              static("simplifytour/js/admin/dynamic_inline.js")]

class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Wraps render with a CSS class for styling.
    """
    dont_use_model_field_default_for_empty_data = True

    def render(self, *args, **kwargs):
        rendered = super(CheckboxSelectMultiple, self).render(*args, **kwargs)
        return mark_safe("<span class='multicheckbox'>%s</span>" % rendered)