from copy import deepcopy

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import NoReverseMatch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from simplifytour.core.admin import TabularDynamicInlineAdmin, DisplayableAdmin, StackedDynamicInlineAdmin
# from simplifytour.pages.admin import PageAdmin
from simplifytour.utils.urls import admin_url

from simplifytour.packages.models import Package, Place, ItineraryItem
from simplifytour.packages.models import TrekPackage, AdventurousPackage, Article, ArticleGalleryImage
from simplifytour.packages.models import Porter, Guide, Price
from .forms import ItineraryForm, PriceDateForm, OtherInfoForm

import logging

logger = logging.getLogger(__name__)



class ItineraryItemInline(TabularDynamicInlineAdmin):
    # template = "admin/includes/dynamic_inline_stacked.html"
    model = Package.itinerary.through

    def __init__(self, *args, **kwargs):
        super(ItineraryItemInline, self).__init__(*args, **kwargs)

        for f in self.form.base_fields.keys():
            if not f in self.fields:
                if self.exclude and f in self.exclude:
                    continue
                self.fields.append(f)


class PackageAddonsInline(TabularDynamicInlineAdmin):
    model = Package.addons.through


class PriceInline(TabularDynamicInlineAdmin):
    # template = "admin/includes/dynamic_inline_stacked.html"
    model = Price


# class PackageAdminForm(DisplayableAdminForm):

#     def clean_slug(self):
#         """
#         Save the old slug to be used later in PageAdmin.save_model()
#         to make the slug change propagate down the page tree.
#         """
#         self.instance._old_slug = self.instance.slug
#         return self.cleaned_data['slug']


class PackageAdmin(DisplayableAdmin):
    """
    Admin class for the ``Package`` model and all subclasses of
    ``Package``. Handles redirections between admin interfaces for the
    ``Package`` model and its subclasses.
    """

    # change_list_template = "admin/packages/package/change_list.html"
    # form = PackageAdminForm
    form = OtherInfoForm
    fieldsets = (
        (None, {
            "fields": [
                "title",
                "provided_by",
                ("status", "publish_date", "expiry_date",),
                ("login_required", "is_featured", "is_archived",),
                ("porter_required", "porter_days", "porters",),
                ("guide_required", "guide_days", "guides",),
                "featured_image",
                "content",
                "include",
                "exclude",
                ("name"),
            ],
        }),
        (_("Meta data"), {
            "fields": [
                "_meta_title",
                "slug",
                ("description", "gen_description"),
                "keywords",
                "in_sitemap"
            ],
            "classes": ("collapse-closed",)
        }),
    )
    filter_horizontal = ("porters", "guides", "addons")
    inlines = (PackageAddonsInline, ItineraryItemInline, PriceInline,)

    readonly_fields = ("other_info",)

    def render_change_form(self, request, *args, obj=None, **kwargs):
        """
        remove
        """
        remove_data = request.GET.get('remove_data', None)
        if not remove_data is None:
            try:
                obj.other_info.remove(remove_data)
                obj.save()
            except:
                pass
        return super(PackageAdmin, self).render_change_form(request, *args, obj=obj, **kwargs)

    def in_menu(self):
        """
        Hide subclasses from the admin menu.
        """
        return self.model is Package

    def _check_permission(self, request, package, permission):
        """
        Runs the custom permission check and raises an
        exception if False.
        """
        if not getattr(package, "can_" + permission)(request):
            raise PermissionDenied

    def add_view(self, request, **kwargs):
        """
        For the ``Page`` model, redirect to the add view for the
        first page model, based on the ``ADD_PAGE_ORDER`` setting.
        """
        if self.model is Package:
            return HttpResponseRedirect(self.get_content_models()[0].add_url)
        return super(PackageAdmin, self).add_view(request, **kwargs)

    def change_view(self, request, object_id, **kwargs):
        """
        For the ``Page`` model, check ``page.get_content_model()``
        for a subclass and redirect to its admin change view.
        Also enforce custom change permissions for the page instance.
        """
        package = get_object_or_404(Package, pk=object_id)
        content_model = package.get_content_model()
        self._check_permission(request, content_model, "change")
        if self.model is Package:
            if content_model is not None:
                change_url = admin_url(content_model.__class__, "change",
                                       content_model.id)
                return HttpResponseRedirect(change_url)
        kwargs.setdefault("extra_context", {})
        kwargs["extra_context"].update({
            "hide_delete_link": not content_model.can_delete(request),
            "hide_slug_field": content_model.overridden(),
        })
        return super(PackageAdmin, self).change_view(request, object_id, **kwargs)

    def delete_view(self, request, object_id, **kwargs):
        """
        Enforce custom delete permissions for the page instance.
        """
        package = get_object_or_404(Package, pk=object_id)
        content_model = package.get_content_model()
        self._check_permission(request, content_model, "delete")
        return super(PackageAdmin, self).delete_view(request, object_id, **kwargs)

    def changelist_view(self, request, extra_context=None):
        """
        Redirect to the ``Page`` changelist view for ``Page``
        subclasses.
        """
        if self.model is not Package:
            return HttpResponseRedirect(admin_url(Package, "changelist"))
        if not extra_context:
            extra_context = {}
        extra_context["package_models"] = self.get_content_models()
        return super(PackageAdmin, self).changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        """
        Set the ID of the parent page if passed in via querystring, and
        make sure the new slug propagates to all descendant pages.
        """
        # if change and obj._old_slug != obj.slug:
        #     new_slug = obj.slug or obj.generate_unique_slug()
        #     obj.slug = obj._old_slug
        #     obj.set_slug(new_slug)

        parent = request.GET.get("parent")
        if parent is not None and not change:
            obj.parent_id = parent
            obj.save()
        super(PackageAdmin, self).save_model(request, obj, form, change)

    def _maintain_parent(self, request, response):
        """
        Maintain the parent ID in the querystring for response_add and
        response_change.
        """
        location = response._headers.get("location")
        parent = request.GET.get("parent")
        if parent and location and "?" not in location[1]:
            url = "%s?parent=%s" % (location[1], parent)
            return HttpResponseRedirect(url)
        return response

    def response_add(self, request, obj):
        """
        Enforce page permissions and maintain the parent ID in the
        querystring.
        """
        response = super(PackageAdmin, self).response_add(request, obj)
        return self._maintain_parent(request, response)

    def response_change(self, request, obj):
        """
        Enforce page permissions and maintain the parent ID in the
        querystring.
        """
        response = super(PackageAdmin, self).response_change(request, obj)
        return self._maintain_parent(request, response)

    @classmethod
    def get_content_models(cls):
        """
        Return all Page subclasses that are admin registered, ordered
        based on the ``ADD_PAGE_ORDER`` setting.
        """
        models = []
        for model in Package.get_content_models():
            try:
                admin_url(model, "add")
            except NoReverseMatch:
                continue
            else:
                setattr(model, "meta_verbose_name", model._meta.verbose_name)
                setattr(model, "add_url", admin_url(model, "add"))
                models.append(model)
        order = [name.lower() for name in settings.ADD_PAGE_ORDER]

        def sort_key(package):
            name = "%s.%s" % (package._meta.app_label, package._meta.object_name)
            unordered = len(order)
            try:
                return (order.index(name.lower()), "")
            except ValueError:
                return (unordered, package.meta_verbose_name)

        return sorted(models, key=sort_key)


class ArticleGalleryImageInline(TabularDynamicInlineAdmin):
    model = ArticleGalleryImage


class ArticleAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("simplifytour/css/admin/gallery.css",)}

    inlines = (ArticleGalleryImageInline,)


class PriceAdmin(admin.ModelAdmin):
    form = PriceDateForm
    list_display = (
    'package', 'standard', 'marked_price', 'discounted_price', 'min_group_size', 'max_group_size', 'price_notes',
    'starting_date')
    fieldsets = (
        (None, {
            "fields": [
                "package",
                "standard",
                "marked_price",
                "discounted_price",
                "reduced_by",
                "booking_amount",
                "min_group_size",
                "max_group_size",
                "price_notes",
                ("starting_date_html", "date"),
                "extra_content",
            ],
        }),
    )
    readonly_fields = ("starting_date_html",)

    def starting_date_html(self, obj):
        date = ["<strong>{0}</strong><a href='?remove_date={0}' class='deletelink'>Delete</a></br>".format(i) for i in
                obj.starting_date]

        return ''.join(date)

    starting_date_html.allow_tags = True

    def render_change_form(self, request, *args, obj=None, **kwargs):
        """
        starting date remove from price
        """
        remove_date = request.GET.get('remove_date', None)
        if not remove_date is None:
            try:
                obj.starting_date.remove(remove_date)
                obj.save()
            except:
                pass
        return super(PriceAdmin, self).render_change_form(request, *args, obj=obj, **kwargs)


class GuideAdmin(admin.ModelAdmin):
    list_display = ('language', 'rate', 'remarks')


class PorterAdmin(admin.ModelAdmin):
    list_display = ('remarks', 'ratio', 'rate', 'count')


admin.site.register(Package, PackageAdmin)
admin.site.register(AdventurousPackage, PackageAdmin)
admin.site.register(TrekPackage, PackageAdmin)
admin.site.register(ItineraryItem)
admin.site.register(Price, PriceAdmin)
admin.site.register(Porter, PorterAdmin)
admin.site.register(Guide, GuideAdmin)
admin.site.register(Place)
admin.site.register(Article, ArticleAdmin)
