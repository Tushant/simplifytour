import re
import unicodedata

from django.urls import reverse, resolve, get_script_prefix
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from django.utils import translation
from django.conf import settings

from simplifytour.utils.importing import import_dotted_path


def admin_url(model, url, object_id=None):
    """
    Returns the URL for the given model and admin url name.
    """
    opts = model._meta
    url = "admin:%s_%s_%s" % (opts.app_label, opts.object_name.lower(), url)
    args = ()
    if object_id is not None:
        args = (object_id,)
    return reverse(url, args=args)


def home_slug():
    """
    Returns the slug arg defined for the ``home`` urlpattern, which
    is the definitive source of the ``url`` field defined for an
    editable homepage object.
    """
    prefix = get_script_prefix()
    slug = reverse("home")
    if slug.startswith(prefix):
        slug = '/' + slug[len(prefix):]
    try:
        return resolve(slug).kwargs["slug"]
    except KeyError:
        return slug


def slugify(s):
    """
    Loads the callable defined by the ``SLUGIFY`` setting, which defaults
    to the ``slugify_unicode`` function.
    """
    return import_dotted_path(settings.SLUGIFY)(s)


def slugify_unicode(s):
    """
    Replacement for Django's slugify which allows unicode chars in
    slugs, for URLs in Chinese, Russian, etc.
    Adopted from https://github.com/mozilla/unicode-slugify/
    """
    chars = []
    for char in str(smart_text(s)):
        cat = unicodedata.category(char)[0]
        if cat in "LN" or char in "-_~":
            chars.append(char)
        elif cat == "Z":
            chars.append(" ")
    return re.sub(r"[-\s]+", "-", "".join(chars).strip()).lower()


def unique_slug(queryset, slug_field, slug):
    """
    Ensures a slug is unique for the given queryset, appending
    an integer to its end until the slug is unique.
    """
    i = 0
    while True:
        if i > 0:
            if i > 1:
                slug = slug.rsplit("-", 1)[0]
            slug = "%s-%s" % (slug, i)
        try:
            queryset.get(**{slug_field: slug})
        except ObjectDoesNotExist:
            break
        i += 1
    return slug


def path_to_slug(path):
    """
    Removes everything from the given URL path, including
    language code and ``PAGES_SLUG`` if any is set, returning
    a slug that would match a ``Page`` instance's slug.
    """
    # from django.urls import PAGES_SLUG
    PAGES_SLUG = ""
    lang_code = translation.get_language_from_path(path)
    for prefix in (lang_code, settings.SITE_PREFIX, PAGES_SLUG):
        if prefix:
            path = path.replace(prefix, "", 1)
    return clean_slashes(path) or "/"


def clean_slashes(path):
    """
    Canonicalize path by removing leading slashes and conditionally
    removing trailing slashes.
    """
    return path.strip("/") if settings.APPEND_SLASH else path.lstrip("/")
