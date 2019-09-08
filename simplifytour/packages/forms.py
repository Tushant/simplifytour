from django import forms
from django.contrib import admin
from .models import ItineraryItem, PackageItinerary, Price, Package
from simplifytour.core.forms import DynamicInlineAdminForm
from django.core import serializers
from django.utils.translation import ugettext as _
import json


class PriceDateForm(forms.ModelForm):

    date = forms.DateField(label=_("Add new date"))

    class Meta:
        model = Price
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(PriceDateForm, self).__init__(*args, **kwargs)
        self.fields['date'].required = False

    def save(self, commit=True):
        starting_date = self.cleaned_data.get('date', None)
        price = super(PriceDateForm, self).save(commit=False)
        if starting_date:
            if not price.starting_date:
                price.starting_date = []
            price.starting_date.append(starting_date)
            price.save()
        return price


class OtherInfoForm(forms.ModelForm):

    name = forms.CharField(label=_("Add other information"))

    class Meta:
        model = Package
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(OtherInfoForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False

    def save(self, commit=True):
        other_info = self.cleaned_data.get('name', None)
        package = super(OtherInfoForm, self).save(commit=False)
        if other_info:
            package.other_info = json.loads(other_info)
            package.save()
        return package


class ItineraryForm(DynamicInlineAdminForm):
    title = forms.CharField(label=_("Title"), required=False)
    description = forms.CharField(label=_("Description"), required=False)

    class Meta:
        model = PackageItinerary
        fields = "__all__"

    def __init__(self, *args, instance=None, initial=None, **kwargs):
        if instance is not None:
            initial = initial or {}
            initial.update({
            'title': instance.item.title,
            'description': instance.item.description,
            })
        return super(ItineraryForm, self).__init__(*args, instance=instance, initial=initial, **kwargs)

    def save(self, commit=True):
        instance = super(ItineraryForm, self).save(commit=commit)

        instance.item.title = self.cleaned_data["title"]
        instance.item.description = self.cleaned_data["description"]
        instance.item.save()

        return instance


class ItinearyPackageForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, help_text=_("Description of the itinary package"))
    price = forms.DecimalField(help_text=_("Price needed for this package"))
    days = forms.DecimalField(help_text=_("No of days required for this itinary item"))
    duration = forms.DecimalField(help_text=_("Time duration taken by this itinary item. 0 for full day."))

    class Meta:
        model = ItineraryItem
        fields = "__all__"




