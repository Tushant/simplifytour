from django.utils.safestring import mark_safe
from django.utils import six
from django import forms

from simplifytour.utils.static import static_lazy as static
from simplifytour.generic.models import Keyword


class KeywordsWidget(forms.MultiWidget):
    """
    Form field for the ``KeywordsField`` generic relation field. Since
    the admin with model forms has no form field for generic
    relations, this form field provides a single field for managing
    the keywords. It contains two actual widgets, a text input for
    entering keywords, and a hidden input that stores the ID of each
    ``Keyword`` instance.
    The attached JavaScript adds behaviour so that when the form is
    submitted, an AJAX post is made that passes the list of keywords
    in the text input, and returns a list of keyword IDs which are
    then entered into the hidden input before the form submits. The
    list of IDs in the hidden input is what is used when retrieving
    an actual value from the field for the form.
    """

    class Media:
        js = (static("simplifytour/js/admin/keywords_field.js"),)

    def __init__(self, attrs=None):
        """
        Setup the text and hidden form field widgets.
        """
        widgets = (forms.HiddenInput,
                   forms.TextInput(attrs={"class": "vTextField"}))
        super(KeywordsWidget, self).__init__(widgets, attrs)
        self._ids = []

    def decompress(self, value):
        """
        Takes the sequence of ``AssignedKeyword`` instances and splits
        them into lists of keyword IDs and titles each mapping to one
        of the form field widgets.
        If the page has encountered a validation error then
        Takes a string with ``Keyword`` ids and fetches the
        sequence of ``AssignedKeyword``
        """
        keywords = None

        if hasattr(value, "select_related"):
            keywords = [a.keyword for a in value.select_related("keyword")]
        elif value and isinstance(value, six.string_types):
            keyword_pks = value.split(",")
            keywords = Keyword.objects.all().filter(id__in=keyword_pks)

        if keywords:
            keywords = [(str(k.id), k.title) for k in keywords]
            self._ids, words = list(zip(*keywords))
            return (",".join(self._ids), ", ".join(words))
        return ("", "")

    def render(self, *args, **kwargs):
        """
        Wraps the output HTML with a list of all available ``Keyword``
        instances that can be clicked on to toggle a keyword.
        """
        rendered = super(KeywordsWidget, self).render(*args, **kwargs)
        links = ""
        for keyword in Keyword.objects.all().order_by("title"):
            prefix = "+" if str(keyword.id) not in self._ids else "-"
            links += ("<a href='#'>%s%s</a>" % (prefix, str(keyword)))
        rendered += mark_safe("<p class='keywords-field'>%s</p>" % links)
        return rendered

    def value_from_datadict(self, data, files, name):
        """
        Return the comma separated list of keyword IDs for use in
        ``KeywordsField.save_form_data()``.
        """
        return data.get("%s_0" % name, "")
