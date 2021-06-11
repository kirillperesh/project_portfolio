from django.apps import AppConfig


class GlykeBackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'glyke_back'

    def ready(self):
        import glyke_back.signals

