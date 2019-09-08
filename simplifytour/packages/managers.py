from django.conf import settings

from simplifytour.core.managers import DisplayableManager
from simplifytour.utils.urls import home_slug


class PackageManager(DisplayableManager):

    def published(self, for_user=None, include_login_required=False):
        """
        Override ``DisplayableManager.published`` to exclude
        pages with ``login_required`` set to ``True``. if the
        user is unauthenticated and the setting
        ``PAGES_PUBLISHED_INCLUDE_LOGIN_REQUIRED`` is ``False``.

        The extra ``include_login_required`` arg allows callers to
        override the ``PAGES_PUBLISHED_INCLUDE_LOGIN_REQUIRED``
        behaviour in special cases where they want to deal with the
        ``login_required`` field manually, such as the case in
        ``PageMiddleware``.
        """
        published = super(PackageManager, self).published(for_user=for_user)
        unauthenticated = for_user and not for_user.is_authenticated()
        if (unauthenticated and not include_login_required and not
        settings.PACKAGES_PUBLISHED_INCLUDE_LOGIN_REQUIRED):
            published = published.exclude(login_required=True)
        return published

    def with_ascendants_for_slug(self, slug, **kwargs):
        """
        Given a slug, returns a list of pages from ascendants to
        descendants, that form the parent/child page relationships
        for that slug. The main concern is to do this in a single
        database query rather than querying the database for parents
        of a given page.

        Primarily used in ``PageMiddleware`` to provide the current
        page, which in the case of non-page views, won't match the
        slug exactly, but will likely match a page that has been
        created for linking to the entry point for the app, eg the
        blog page when viewing blog posts.

        Also used within ``Page.get_ascendants``, which gets called
        in the ``pages.views`` view, for building a list of possible
        templates that can be used for the page.

        If a valid chain of pages is found, we also assign the pages
        to the ``page._ascendants`` attr of the main/first/deepest
        page, so that when its ``get_ascendants`` method is called,
        the ascendants chain can be re-used without querying the
        database again. This occurs at least once, given the second
        use-case described above.
        """

        if slug == "/":
            slugs = [home_slug()]
        else:

            parts = slug.split("/")
            slugs = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]

        packages_for_user = self.published(**kwargs)
        packages = list(packages_for_user.filter(slug__in=slugs).order_by("-slug"))
        if not packages:
            return []

        packages[0]._ascendants = []
        for i, package in enumerate(packages):
            try:
                parent = packages[i + 1]
            except IndexError:

                if package.parent_id:
                    break  # Invalid parent
            else:
                if package.parent_id != parent.id:
                    break  # Invalid parent
        else:
            packages[0]._ascendants = packages[1:]
        return packages

    def with_ascendants_for_keyword(self, slug, **kwargs):
        return self.published(**kwargs)
