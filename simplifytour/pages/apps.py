from django.apps import AppConfig


class PagesConfig(AppConfig):

    name = 'simplifytour.pages'

    def ready(self):
        from . import checks  # noqa
