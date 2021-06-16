from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify

from .forms import AddProductForm, PhotosForm, SelectCategoryProductForm
from .models import Category, Product
from photologue import models as photo_models


def create_gallery(*, title):
    """Creates and returns a photologue gallery by name
    Can't use get_or_create and have to specify slug because of some photologue bug"""
    gallery_title = title + _("_gallery")
    gallery_slug = slugify(gallery_title)
    return photo_models.Gallery.objects.create(title=gallery_title, slug=gallery_slug)



# TODO Devide into several functions and add comment and docstr
# TODO add 404 if not staff
@require_http_methods(["GET", "POST"])
def add_product_dynamic_view(request):
    if not Category.objects.filter(is_active=True): return HttpResponse(_('No active categories'))

    photos_form = PhotosForm(request.POST, request.FILES)
    product_form = AddProductForm(request.POST or None) if 'name' in request.POST else AddProductForm()
    context = {
        'category_form': SelectCategoryProductForm(request.POST or None),
        'photos_form': photos_form,
        'product_form': product_form,}

    if request.method == 'POST':
        if 'category' in request.POST:
            category_fields = {}
            context['category'] = request.POST['category']
            category = Category.objects.get(id=context['category'])

            for filter in category.filters.all():
                # TODO Add some king of validation here to select the right input field
                category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},), label=_(str(filter).capitalize()))

        CategoryFiltersForm = type('CategoryFiltersForm', (forms.Form,), category_fields)
        filters_form = CategoryFiltersForm(request.POST or None)
        context['filter_form'] = filters_form

        if all([filters_form.is_valid(), product_form.is_valid(),]):
            new_product = Product.objects.create(name=product_form.cleaned_data['name'],
                                                 description=product_form.cleaned_data['description'],
                                                 created_by = request.user,
                                                 category=category,
                                                 # tags,
                                                 stock=product_form.cleaned_data['stock'],
                                                 photos=create_gallery(title=product_form.cleaned_data['name']),
                                                 attributes=filters_form.cleaned_data,
                                                 cost_price=product_form.cleaned_data['cost_price'],
                                                 selling_price=product_form.cleaned_data['selling_price'],
                                                 discount_percent=product_form.cleaned_data['discount_percent'],
                                                )
            # tags block
            new_product.tags.add(*product_form.cleaned_data['tags']) # using list as multiple positional arguments

            # photos block
            if photos_form.is_valid():
                for image in request.FILES.getlist('photos'):
                    image_name = image.name + f'_{new_product.name}'
                    if photo_models.Photo.objects.filter(title=image_name).exists():
                        image_name += f'_{photo_models.Photo.objects.filter(title=image_name).count()}'
                    # TODO add any photologue filters here
                    photo = photo_models.Photo.objects.create(image=image, title=image_name, slug=slugify(image_name))
                    new_product.photos.photos.add(photo)
            else:
                # TODO add this url and view
                return redirect(reverse('smth_went_wrong'), error_suffix='photos')

            # TODO add redirect on success
    return render(request, "add_product.html", context)

