from django.contrib import admin
from django.apps import apps

from .models import Tile


# models = apps.get_models()

# for model in models:
#     try:
#         admin.site.register(model)
#     except admin.sites.AlreadyRegistered:
#         pass

class ReadonlyAdmin(admin.ModelAdmin):
    readonly_fields = ('time_created', 'last_modified')

admin.site.register(Tile, ReadonlyAdmin)
