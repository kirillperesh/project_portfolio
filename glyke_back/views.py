from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods


from django.utils.text import slugify

from .forms import AddProductForm, PhotosForm, SelectCategoryProductForm
from .models import Category, Product
from photologue import models as photo_models


# TODO Devide into several functions and add comment and docstr
# TODO add 404 if not staff
@require_http_methods(["GET", "POST"])
def add_product_dynamic_view(request):
    if not Category.objects.filter(is_active=True): return HttpResponse(_('No active categories'))

    context = {}
    if request.method == 'POST':
        # photo_models.Photo.objects.all().delete()
        # img = request.FILES['photos']
        # print(request.FILES['photos'])
        # print(type(request.FILES['photos']))
        # print(img.name)
        # photo_models.Photo.objects.get_or_create(image=img, title=img.name, slug=slugify(img.name))

        # photos_form = PhotosForm(request.POST, request.FILES)
        # context['photos_form'] = photos_form
        # if photos_form.is_valid():
        #     gallery = photo_models.Gallery.objects.get(title='test')

        #     for img in request.FILES.getlist('photos'):
        #         if not photo_models.Photo.objects.filter(title=img.name).exists():
        #             print('gets here')
        #             photo = photo_models.Photo.objects.create(image=img, title=img.name, slug=slugify(img.name))
        #             gallery.photos.add(photo)

        if 'category' in request.POST:
            category_fields = {}
            context['category'] = request.POST['category']
            category = Category.objects.get(id=context['category'])

            for filter in category.filters.all():
                # TODO Add some king of validation here to select the right input field
                category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},), label=_(str(filter).capitalize()))

        CategoryFiltersForm = type('CategoryFiltersForm',
                                   (forms.Form,),
                                   category_fields)
        context['filter_form'] = CategoryFiltersForm()
        filters_form = CategoryFiltersForm(request.POST or None)
        product_form = AddProductForm(request.POST or None)

        if all([filters_form.is_valid(), product_form.is_valid(),]):
            new_product = Product.objects.create(name=product_form.cleaned_data['name'],
                                                 description=product_form.cleaned_data['description'],
                                                 created_by = request.user,
                                                 category=category,
                                                 # tags,
                                                 stock=product_form.cleaned_data['stock'],
                                                 # photos='placeholder',
                                                 attributes=filters_form.cleaned_data,
                                                 cost_price=product_form.cleaned_data['cost_price'],
                                                 selling_price=product_form.cleaned_data['selling_price'],
                                                 discount_percent=product_form.cleaned_data['discount_percent'],
                                                )
            new_product.tags.add(*product_form.cleaned_data['tags']) # using list as multiple positional arguments

            # photos block
            gallery_title = product_form.cleaned_data['name'] + _("'s gallery")
            gallery_slug = slugify(gallery_title)
            gallery = photo_models.Gallery.objects.create(title=gallery_title, slug=gallery_slug)



            # TODO add redirect on success
        else:
            context['category_form'] = SelectCategoryProductForm(request.POST or None)
            context['filter_form'] = CategoryFiltersForm(request.POST or None)
            context['product_form'] = AddProductForm(request.POST or None) if 'name' in request.POST else AddProductForm() # makes sure "required" errors don't show before any input
            return render(request, "add_product.html", context)



    # context['photos_form'] = PhotosForm(request.POST, request.FILES)



    context['category_form'] = SelectCategoryProductForm()
    context['product_form'] = AddProductForm()
    return render(request, "add_product.html", context)

