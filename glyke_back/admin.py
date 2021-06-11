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


# from .models import Category, Product
# test_parent_1 = Category.objects.get_or_create(name='test parent 1')[0]
# test_parent_2 = Category.objects.get_or_create(name='test parent 2')[0]
# test_parent_1.parent = test_parent_2
# test_parent_1.save()
# child11 = Category.objects.get_or_create(name='test child 1 1')[0]
# child11.parent = test_parent_1
# child11.save()
# child12 = Category.objects.get_or_create(name='test child 1 2')[0]
# child12.parent = test_parent_1
# child12.save()

# product11 = Product.objects.get_or_create(name='test product 1 1')[0]
# product11.category = test_parent_1
# product11.save()
# product12 = Product.objects.get_or_create(name='test product 1 2')[0]
# product12.category = None
# product12.save()
