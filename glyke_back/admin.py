from django.contrib import admin
from django.apps import apps


class TempAdmin(admin.ModelAdmin):
    exclude_fields = ['id', 'modified', ]
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name not in self.exclude_fields]
        super(TempAdmin, self).__init__(model, admin_site)

models = apps.get_models()
for model in models:
    try:
        admin.site.register(model, TempAdmin)
    except admin.sites.AlreadyRegistered:
        pass


