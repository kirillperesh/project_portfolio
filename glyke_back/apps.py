from django.apps import AppConfig


class GlykeBackConfig(AppConfig):
    name = 'glyke_back'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import glyke_back.signals

