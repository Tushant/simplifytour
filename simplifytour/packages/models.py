import os
from urllib.parse import urljoin
from future.utils import native
from jsonfield import JSONField
from string import punctuation
from zipfile import ZipFile
from io import BytesIO

from django.utils.translation import ugettext, ugettext_lazy as _
# from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.urls import reverse
from django.apps import apps
from django.db import models

from simplifytour.core.models import Displayable, Orderable, RichText
from simplifytour.core.fields import FileField, RichTextField
from simplifytour.utils.importing import import_dotted_path
from simplifytour.generic.fields import RatingField
from simplifytour.utils.urls import path_to_slug
from simplifytour.utils.models import upload_to
# from simplifytour.pages.models import Page
from .managers import PackageManager
# from .fields import MenusField

'''
list your packages. Unauthenticated user can also list packages where first new user will be created and isConfirmed false
when user activates his/her account then only the listed packages will be published otherwise will be kept in draft
'''


class BasePackage(Orderable, Displayable):
    """
    Exists solely to store ``packageManager`` as the main manager.
    If it's defined on ``package``, a concrete model, then each
    ``package`` subclass loses the custom manager.
    """

    objects = PackageManager()

    class Meta:
        abstract = True


class Package(BasePackage):
    """
    A package in the package tree. This is the base class that custom content types
    need to subclass.
    """

    parent = models.ForeignKey("Package", blank=True, null=True, related_name="children", on_delete=models.CASCADE)
    titles = models.CharField(editable=False, max_length=1000, null=True)
    content_model = models.CharField(editable=False, max_length=50, null=True)
    login_required = models.BooleanField(_("Login required"), default=False,
                                         help_text=_("If checked, only logged in users can view this Package"))
    itinerary = models.ManyToManyField('ItineraryItem', through="PackageItinerary")
    addons = models.ManyToManyField('ItineraryItem', through="PackageAddons", related_name="addon_packages_set",
                                    blank=True)
    # related_blog_posts = models.ManyToManyField(BlogPost, verbose_name=_("Related Blog posts"), blank=True)

    content = RichTextField(_("Content"))
    include = RichTextField(_("Include"))
    exclude = RichTextField(_("Exclude"))

    featured_image = FileField(blank=True, null=True, upload_to='featured_images',
                               help_text=_("Focal image for this package."))

    provided_by = models.ForeignKey(get_user_model(),
                                    help_text=_("Provider of this Package"), on_delete=models.CASCADE)
    is_featured = models.BooleanField(_("Is Featured"), default=False,
                                      help_text=_("Show in Homepage?"))

    is_archived = models.BooleanField(_("Is Archived"), default=False,
                                      help_text=_("Archive this package?"))

    porter_required = models.BooleanField(_("Porter required"), default=False,
                                          help_text=_("Is porter necessary for this package?"))

    porter_days = models.IntegerField(default=0,
                                      help_text=_("If porter is necessary, for how many days?"))

    porters = models.ManyToManyField("Porter", related_name="packages", blank=True,
                                     help_text=_("Porter options for this Package"))

    guide_required = models.BooleanField(_("Guide required"), default=False,
                                         help_text=_("Is Guide necessary for this package?"))

    guide_days = models.IntegerField(default=0,
                                     help_text=_("If guide is necessary, for how many days?"))

    guides = models.ManyToManyField("Guide", related_name="packages", blank=True,
                                    help_text=_("Guide options for this Package"))

    other_info = JSONField(default=[], blank=False, null=False, editable=False,
                           help_text=_("Other information of package"))

    rating = RatingField(verbose_name=_("Rating"))

    @property
    def days(self):
        total_days = 0
        for iti_day in self.itinerary.all():
            total_days += iti_day.days
        return total_days

    @property
    def porter(self):
        return self.default_porter

    @property
    def default_porter(self):
        if self.porters.count() > 0:
            return self.porters.all()[0]

    @property
    def default_guide(self):
        if self.guides.count() > 0:
            return self.guides.all()[0]

    class Meta:
        verbose_name = _("Package")
        verbose_name_plural = _("Packages")
        ordering = ("title",)
        # order_with_respect_to = "parent"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Create the titles field using the titles up the parent chain
        and set the initial value for ordering.
        """
        if self.id is None:
            self.content_model = self._meta.object_name.lower()
        self.titles = self.title
        super(Package, self).save(*args, **kwargs)

    def description_from_content(self):
        """
        Return first 40 words as summarized description.
        """

        return " ".join(self.content.split()[:40])

    # def get_absolute_url(self):
    #     """
    #     URL for a package - for ``Link`` package types, simply return its
    #     slug since these don't have an actual URL pattern. Also handle
    #     the special case of the homepackage being a package object.
    #     """
    #     slug = self.slug
    #     if self.content_model == "link":
    #         slug = urljoin('/', slug)
    #         return slug
    #     if slug == "/":
    #         return reverse("home")
    #     else:
    #         return reverse("package", kwargs={"slug": slug})

    def get_ascendants(self, for_user=None):
        """
        Returns the ascendants for the Package. Ascendants are cached in
        the ``_ascendants`` attribute, which is populated when the Package
        is loaded via ``Package.objects.with_ascendants_for_slug``.
        """
        if not self.parent_id:
            return []
        if not hasattr(self, "_ascendants"):
            if self.slug:
                kwargs = {"for_user": for_user}
                packages = Package.objects.with_ascendants_for_slug(self.slug,
                                                                    **kwargs)
                self._ascendants = packages[0]._ascendants
            else:
                self._ascendants = []
        if not self._ascendants:
            child = self
            while child.parent_id is not None:
                self._ascendants.append(child.parent)
                child = child.parent
        return self._ascendants

    @classmethod
    def get_content_models(cls):
        """
        Return all Package subclasses.
        """
        is_content_model = lambda m: m is not Package and issubclass(m, Package)
        return list(filter(is_content_model, apps.get_models()))

    def get_content_model(self):
        """
        Provies a generic method of retrieving the instance of the custom
        content type's model for this Package.
        """
        return getattr(self, self.content_model, None)
    
    def overridden(self):
        """
        Returns ``True`` if the package's slug has an explicitly defined
        urlpattern and is therefore considered to be overridden.
        """
        pass
        # from packages.views import package
        # package_url = reverse("package", kwargs={"slug": self.slug})
        # resolved_view = resolve(package_url)[0]
        # return resolved_view != package

    def can_add(self, request):
        """
        Dynamic ``add`` permission for content types to override.
        """
        return self.slug != "/"

    def can_change(self, request):
        """
        Dynamic ``change`` permission for content types to override.
        """
        return True

    def can_delete(self, request):
        """
        Dynamic ``delete`` permission for content types to override.
        """
        return True

    def can_move(self, request, new_parent):
        """
        Dynamic ``move`` permission for content types to override. Controls
        whether a given page move in the page tree is permitted. When the
        permission is denied, raises a ``PageMoveException`` with a single
        argument (message explaining the reason).
        """
        pass

    def set_helpers(self, context):
        """
        Called from the ``page_menu`` template tag and assigns a
        handful of properties based on the current page, that are used
        within the various types of menus.
        """
        current_package = context["_current_package"]
        current_package_id = getattr(current_package, "id", None)
        current_parent_id = getattr(current_package, "parent_id", None)
        self.is_current_child = self.parent_id == current_package_id
        self.is_child = self.is_current_child
        self.is_current_sibling = self.parent_id == current_parent_id
        try:
            request = context["request"]
        except KeyError:
            self.is_current = False
        else:
            self.is_current = self.slug == path_to_slug(request.slug)

        def is_c_or_a(package_id):
            parent_id = context.get("_parent_package_ids", {}).get(package_id)
            return self.id == package_id or (parent_id and is_c_or_a(parent_id))

        self.is_current_or_ascendant = lambda: bool(is_c_or_a(current_package_id))
        self.is_current_parent = self.id == current_parent_id
        self.is_primary = self.parent_id is None
        self.html_id = self.slug.replace("/", "-")
        self.branch_level = 0

    def get_template_name(self):
        """
        Subclasses can implement this to provide a template to use
        in ``package.views.page``.
        """
        return None

    def in_menu_template(self, template_name):
        if self.in_menus is not None:
            for i, l, t in settings.PAGE_MENU_TEMPLATES:
                if not str(i) in self.in_menus and t == template_name:
                    return False
        return True


class PackageAddons(models.Model):
    package = models.ForeignKey('Package', on_delete=models.CASCADE)
    item = models.ForeignKey('ItineraryItem', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('package', 'item',)

    @property
    def title(self):
        return self.item.title

    def __str__(self):
        return "{}".format(self.item.title)


class PackageItinerary(Orderable):
    package = models.ForeignKey('Package', on_delete=models.CASCADE)
    item = models.ForeignKey('ItineraryItem', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('package', 'item',)

    @property
    def title(self):
        return self.item.title

    def __str__(self):
        return "{}".format(self.item.title)


class Place(models.Model):
    """
    This place is foregin key to Itenary item starting_place and ending_place
    """
    name = models.CharField(max_length=255, blank=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")


class ItineraryItem(models.Model):
    """
    A day in a package.
    """

    title = models.CharField(max_length=255, blank=False,
                             help_text=_("Itinary title"))
    description = models.TextField(max_length=255, blank=False,
                                   help_text=_("Brief description"))
    starting_place = models.ForeignKey("Place", blank=True, null=True, default=None, related_name="stating_place",
                                       help_text=_("Where does it start from?"), on_delete=models.CASCADE)
    ending_place = models.ForeignKey("Place", blank=True, null=True, default=None, related_name="ending_place",
                                     help_text=_("Where will it end?"), on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=None,
                                help_text=_("Price, just in case this single Itenary is requested."))
    days = models.DecimalField(decimal_places=2, max_digits=5, default=1,
                               help_text=_("No of days required for this Itenary."))
    duration = models.DecimalField(decimal_places=2, max_digits=5, default=0,
                                   help_text=_("Time duration taken by this itinary item. 0 for full day."))
    starting_time = models.TimeField(null=True, default=None,
                                     help_text=_("Information purpose only. When will it start from, time of day?"))
    end_time = models.TimeField(null=True, default=None,
                                help_text=_("Information purpose only. When is it supposed to complete, time of day?"))
    provided_by = models.ForeignKey(get_user_model(),
                                    help_text=_("Agency, who provided this itenary."), on_delete=models.CASCADE)

    packages = models.ManyToManyField('Package', through="PackageItinerary")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Itinary Item")
        verbose_name_plural = _("Itinary Items")


class TrekPackage(Package):
    """
    Package for Trekking.
    """

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Trekking Package")
        verbose_name_plural = _("Trekking Packages")


class AdventurousPackage(Package):
    """
    Package for Adventurous.
    """

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Adventurous Package")
        verbose_name_plural = _("Adventurous Packages")


class PackageMoveException(Exception):
    """
    Raised by ``can_move()`` when the move permission is denied. Takes
    an optinal single argument: a message explaining the denial.
    """

    def __init__(self, msg=None):
        self.msg = msg or ugettext("Illegal package move")

    def __str__(self):
        return self.msg

    __unicode__ = __str__


BUDGET_COST = 1
STANDARD_COST = 2
LUXURY_COST = 3
ROOM_TYPES_CHOICES = (
    (BUDGET_COST, _("Budget")),
    (STANDARD_COST, _("Standard")),
    (LUXURY_COST, _("Luxury")),
)

ROOM_TYPES_CHOICES_LOOKUP = {}
for k, v in ROOM_TYPES_CHOICES:
    ROOM_TYPES_CHOICES_LOOKUP[k] = v


class Price(models.Model):
    """
    Price in a package.
    """
    package = models.ForeignKey('Package', related_name='prices', on_delete=models.CASCADE)
    standard = models.IntegerField(choices=ROOM_TYPES_CHOICES, default=BUDGET_COST,
                                   help_text=_("Standard room type available"))
    marked_price = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=None,
                                       help_text=_("Marked price for this package"))
    discounted_price = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=None,
                                           help_text=_("Discount price for this package"))
    price_notes = models.CharField(max_length=255, blank=False,
                                   help_text=_("Notes e.g seasonal and other"))
    min_group_size = models.PositiveSmallIntegerField(default=1, null=False,
                                                      help_text=_("Minimun number of people on this package"))
    reduced_by = models.DecimalField(decimal_places=1, max_digits=3, null=True, default=None,
                                     help_text=_("Discount percentace of this package"))
    booking_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, default=None,
                                         help_text=_("Price given on booking"))
    max_group_size = models.PositiveSmallIntegerField(null=False, default=None,
                                                      help_text=_("Maximum number of people on this package"))
    starting_date = JSONField(default=[], blank=False, null=False,
                              help_text=_("Starting date of package"))
    extra_content = RichTextField(_("Extra Content"), null=True, default=None, blank=True,
                                  help_text=_("Include and Exclude on price"))
    is_archived = models.BooleanField(default=False,
                                      help_text=_("Archive this Price?"))

    def __str__(self):
        return "{} [Rs.{} x {}]".format(self.package.title, self.discounted_price, self.min_group_size)

    @property
    def standard_text(self):
        try:
            return ROOM_TYPES_CHOICES_LOOKUP[int(self.standard)]
        except:
            # TODO mail_admin
            # This return should never be reached
            return "Undefined"

    class Meta:
        verbose_name = _("Price")
        verbose_name_plural = _("Prices")
        # expensive one will come first
        ordering = ['package', '-discounted_price']


class Porter(models.Model):
    """
    Number of porter required.
    """
    ratio = models.DecimalField(decimal_places=1, max_digits=3, null=True, default=None,
                                help_text=_("Traveller to Porter ratio. (eg: 2 means 1 Porter for 2 Travellers)"))
    count = models.IntegerField(null=False, default=0,
                                help_text=_("No. of porters available in our system. 0 refers to unlimited"))
    rate = models.DecimalField(decimal_places=2, max_digits=6, null=True, default=None,
                               help_text=_("Rate of the porter"))
    remarks = models.TextField(max_length=255, default=None,
                               help_text=_("Any notes"))

    def __str__(self):
        return self.remarks

    class Meta:
        verbose_name = _("Porter")
        verbose_name_plural = _("Porters")


class Guide(models.Model):
    """
    Guide to the traveller.
    """
    language = models.CharField(max_length=255, default=None,
                                help_text=_("Language spoken by Guide"))
    rate = models.DecimalField(decimal_places=2, max_digits=6, null=True, default=None,
                               help_text=_("Daily Rate"))
    remarks = models.TextField(max_length=255, default=None,
                               help_text=_("Any notes"))

    def __str__(self):
        return self.remarks

    class Meta:
        verbose_name = _("Guide")
        verbose_name_plural = _("Guides")


GALLERIES_UPLOAD_DIR = "packages"
if settings.PACKAGE_NAME_FILEBROWSER in settings.INSTALLED_APPS:
    fb_settings = "%s.settings" % settings.PACKAGE_NAME_FILEBROWSER
    try:
        GALLERIES_UPLOAD_DIR = import_dotted_path(fb_settings).DIRECTORY
    except ImportError:
        pass


class Article(RichText):
    """
    Page bucket for article-gallery photos.
    """

    zip_import = models.FileField(verbose_name=_("Zip import"), blank=True,
                                  upload_to=upload_to("packages.Article.zip_import", "packages"),
                                  help_text=_("Upload a zip file containing images, and "
                                              "they'll be imported into this article-gallery."))
    featured_image = FileField(blank=True, null=True, upload_to='featured_images',
                               help_text=_("Featured image is displayed"))

    is_featured = models.BooleanField(_("Is Featured"), default=False,
                                      help_text=_("Featured atricles are displayed"))
    rating = RatingField()

    class Meta:
        verbose_name = _("Article page")
        verbose_name_plural = _("Article pages")
        permissions = (
            ('can_view', 'Can View'),
            ('can_modify', 'Can Modify'),
        )

    def get_ascendants(self, for_user=None):
        """
        Returns the ascendants for the Article. Ascendants are cached in
        the ``_ascendants`` attribute, which is populated when the Article
        is loaded via ``Article.objects.with_ascendants_for_slug``.
        """
        if not self.parent_id:
            return []
        if not hasattr(self, "_ascendants"):
            if self.slug:
                kwargs = {"for_user": for_user}
                articles = Article.objects.with_ascendants_for_slug(self.slug,
                                                                    **kwargs)
                self._ascendants = articles[0]._ascendants
            else:
                self._ascendants = []
        if not self._ascendants:
            child = self
            while child.parent_id is not None:
                self._ascendants.append(child.parent)
                child = child.parent
        return self._ascendants

    def save(self, delete_zip_import=True, *args, **kwargs):
        """
        If a zip file is uploaded, extract any images from it and add
        them to the article-gallery, before removing the zip file.
        """
        super(Article, self).save(*args, **kwargs)
        if self.zip_import:
            zip_file = ZipFile(self.zip_import)
            for name in zip_file.namelist():
                data = zip_file.read(name)
                try:
                    from PIL import Image
                    image = Image.open(BytesIO(data))
                    image.load()
                    image = Image.open(BytesIO(data))
                    image.verify()
                except ImportError:
                    pass
                except:
                    continue
                name = os.path.split(name)[1]
                if isinstance(name, bytes):
                    tempname = name.decode('utf-8')
                else:
                    tempname = name

                slug = self.slug if self.slug != "/" else ""
                path = os.path.join(GALLERIES_UPLOAD_DIR, slug, tempname)
                try:
                    saved_path = default_storage.save(path, ContentFile(data))
                except UnicodeEncodeError:
                    from warnings import warn
                    warn("A file was saved that contains unicode "
                         "characters in its path, but somehow the current "
                         "locale does not support utf-8. You may need to set "
                         "'LC_ALL' to a correct value, eg: 'en_US.UTF-8'.")
                    path = os.path.join(GALLERIES_UPLOAD_DIR, slug,
                                        native(str(name, errors="ignore")))
                    saved_path = default_storage.save(path, ContentFile(data))
                self.images.add(ArticleGalleryImage(file=saved_path))
            if delete_zip_import:
                zip_file.close()
                self.zip_import.delete(save=True)


class ArticleGalleryImage(Orderable):
    article = models.ForeignKey("Article", related_name="images", on_delete=models.CASCADE)
    file = FileField(_("File"), max_length=200, format="Image",
                     upload_to=upload_to("packages.ArticleGalleryImage.file", "packages"))
    title = models.CharField(_("Title"), max_length=255, blank=True)
    description = models.CharField(_("Description"), max_length=1000, blank=True)

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        """
        If no description is given when created, create one from the
        file name.
        """

        if not self.id and not self.title:
            name = force_text(self.file.name)
            name = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            name = name.replace("'", "")
            name = "".join([c if c not in punctuation else " " for c in name])
            name = "".join([s.upper() if i == 0 or name[i - 1] == " " else s
                            for i, s in enumerate(name)])
            self.title = name

        if not self.id and not self.description:
            self.description = self.title

        super(ArticleGalleryImage, self).save(*args, **kwargs)




