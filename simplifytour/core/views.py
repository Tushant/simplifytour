import os
import mimetypes

try:
    from urllib.parse import urljoin, urlparse
except ImportError:
    from urlparse import urljoin, urlparse
from json import dumps

from django.contrib.admin.views.decorators import staff_member_required
from django.http import (HttpResponse, HttpResponseNotFound)
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles import finders

from simplifytour.core.models import Displayable
from simplifytour.conf import settings


@staff_member_required
def static_proxy(request):
    """
    Serves TinyMCE plugins inside the inline popups and the uploadify
    SWF, as these are normally static files, and will break with
    cross-domain JavaScript errors if ``STATIC_URL`` is an external
    host. URL for the file is passed in via querystring in the inline
    popup plugin template, and we then attempt to pull out the relative
    path to the file, so that we can serve it locally via Django.
    """
    normalize = lambda u: ("//" + u.split("://")[-1]) if "://" in u else u
    url = normalize(request.GET["u"])
    host = "//" + request.get_host()
    static_url = normalize(settings.STATIC_URL)
    for prefix in (host, static_url, "/"):
        if url.startswith(prefix):
            url = url.replace(prefix, "", 1)
    response = ""
    (content_type, encoding) = mimetypes.guess_type(url)
    if content_type is None:
        content_type = "application/octet-stream"
    path = finders.find(url)
    if path:
        if isinstance(path, (list, tuple)):
            path = path[0]
        if url.endswith(".htm"):
            # Inject <base href="{{ STATIC_URL }}"> into TinyMCE
            # plugins, since the path static files in these won't be
            # on the same domain.
            static_url = settings.STATIC_URL + os.path.split(url)[0] + "/"
            if not urlparse(static_url).scheme:
                static_url = urljoin(host, static_url)
            base_tag = "<base href='%s'>" % static_url
            with open(path, "r") as f:
                response = f.read().replace("<head>", "<head>" + base_tag)
        else:
            try:
                with open(path, "rb") as f:
                    response = f.read()
            except IOError:
                return HttpResponseNotFound()
    return HttpResponse(response, content_type=content_type)

def displayable_links_js(request):
    """
    Renders a list of url/title pairs for all ``Displayable`` subclass
    instances into JSON that's used to populate a list of links in
    TinyMCE.
    """
    links = []
    if "simplifytour.pages" in settings.INSTALLED_APPS:
        from simplifytour.pages.models import Page
        is_page = lambda obj: isinstance(obj, Page)
    else:
        is_page = lambda obj: False
    # For each item's title, we use its model's verbose_name, but in the
    # case of Page subclasses, we just use "Page", and then sort the items
    # by whether they're a Page subclass or not, then by their URL.
    for url, obj in Displayable.objects.url_map(for_user=request.user).items():
        title = getattr(obj, "titles", obj.title)
        real = hasattr(obj, "id")
        page = is_page(obj)
        if real:
            verbose_name = _("Page") if page else obj._meta.verbose_name
            title = "%s: %s" % (verbose_name, title)
        links.append((not page and real, {"title": str(title), "value": url}))
    sorted_links = sorted(links, key=lambda link: (link[0], link[1]['value']))
    return HttpResponse(dumps([link[1] for link in sorted_links]))