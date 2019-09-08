from html.parser import HTMLParser


class HTMLParseError(Exception):
    pass


SELF_CLOSING_TAGS = ['br', 'img']
LOW_FILTER_TAGS = ("iframe", "embed", "video", "param", "source", "object")
LOW_FILTER_ATTRS = ("allowfullscreen", "autostart", "loop", "hidden",
                    "playcount", "volume", "controls", "data", "classid")


class TagCloser(HTMLParser):
    """
    HTMLParser that closes open tags. Takes a HTML string as its first
    arg, and populate a ``html`` attribute on the parser with the
    original HTML arg and any required closing tags.
    """

    def __init__(self, html):
        HTMLParser.__init__(self)
        self.html = html
        self.tags = []
        try:
            self.feed(self.html)
        except HTMLParseError:
            pass
        else:
            self.html += "".join(["</%s>" % tag for tag in self.tags])

    def handle_starttag(self, tag, attrs):
        if tag not in SELF_CLOSING_TAGS:
            self.tags.insert(0, tag)

    def handle_endtag(self, tag):
        try:
            self.tags.remove(tag)
        except ValueError:
            pass


def escape(html):
    """
    Escapes HTML according to the rules defined by the settings
    ``RICHTEXT_FILTER_LEVEL``, ``RICHTEXT_ALLOWED_TAGS``,
    ``RICHTEXT_ALLOWED_ATTRIBUTES``, ``RICHTEXT_ALLOWED_STYLES``.
    """
    from bleach import clean, ALLOWED_PROTOCOLS
    from django.conf import settings
    from simplifytour.core import defaults
    if settings.RICHTEXT_FILTER_LEVEL == defaults.RICHTEXT_FILTER_LEVEL_NONE:
        return html
    tags = settings.RICHTEXT_ALLOWED_TAGS
    attrs = settings.RICHTEXT_ALLOWED_ATTRIBUTES
    styles = settings.RICHTEXT_ALLOWED_STYLES
    if settings.RICHTEXT_FILTER_LEVEL == defaults.RICHTEXT_FILTER_LEVEL_LOW:
        tags += LOW_FILTER_TAGS
        attrs += LOW_FILTER_ATTRS
    if isinstance(attrs, tuple):
        attrs = list(attrs)
    return clean(html, tags=tags, attributes=attrs, strip=True,
                 strip_comments=False, styles=styles,
                 protocols=ALLOWED_PROTOCOLS + ["tel"])
