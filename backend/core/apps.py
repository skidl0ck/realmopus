from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from . import xhtml2pdf_patches
        xhtml2pdf_patches.apply()