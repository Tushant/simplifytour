from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from simplifytour.core.models import SiteRelated


class Setting(SiteRelated):
    """
    Stores values for ``simplifytour.conf`` that can be edited via the admin.
    """

    name = models.CharField(max_length=50)
    value = models.CharField(max_length=2000)

    class Meta:
        verbose_name = _("Setting")
        verbose_name_plural = _("Settings")

    def __str__(self):
        return "%s: %s" % (self.name, self.value)
