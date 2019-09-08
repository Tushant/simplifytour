from string import punctuation

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from simplifytour.generic.models import Keyword


@staff_member_required
def admin_keywords_submit(request):
    """
    Adds any new given keywords from the custom keywords field in the
    admin, and returns their IDs for use when saving a model with a
    keywords field.
    """
    keyword_ids, titles = [], []
    remove = punctuation.replace("-", "")  # Strip punctuation, allow dashes.
    for title in request.POST.get("text_keywords", "").split(","):
        title = "".join([c for c in title if c not in remove]).strip()
        if title:
            kw, created = Keyword.objects.get_or_create_iexact(title=title)
            keyword_id = str(kw.id)
            if keyword_id not in keyword_ids:
                keyword_ids.append(keyword_id)
                titles.append(title)
    return HttpResponse("%s|%s" % (",".join(keyword_ids), ", ".join(titles)),
        content_type='text/plain')
