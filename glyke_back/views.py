from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify
from urllib.parse import urlencode
from django.views.generic import ListView

from photologue import models as photo_models
from .forms import AddProductForm, PhotosForm, SelectCategoryProductForm
from .models import Category, Product
from .glyke_decorators import user_is_staff_or_404


def create_gallery(*, title):
    """Creates and returns a photologue gallery by name
    Can't use get_or_create and have to specify slug because of some photologue bug"""
    gallery_title = title + _("_gallery")
    gallery_slug = slugify(gallery_title)
    return photo_models.Gallery.objects.create(title=gallery_title, slug=gallery_slug)

def get_category_fields(*, category=None):
    category_fields = {}
    if category:
        for filter in category.filters.all(): # these are django-taggit objects
                    # TODO Add some king of validation here to select the right input field
                    category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},),
                                                                                          label=_(str(filter).capitalize()))
    return category_fields


@user_is_staff_or_404()
@require_http_methods(["GET", "POST"])
def add_product_dynamic_view(request):
    """ If all the input is valid creates Product instance, photologue.Gallery instance (title=Product.name + _gallery),
    associates it with product created, and, if provided, associates uploaded images with the gallery.
    Passes selected 'category' as a parameter to the template so it's not lost when submitting main form
    (category selecting is done via separate form).
    """
    # not sure if there may be no categories at any moment
    # if not Category.objects.filter(is_active=True): return HttpResponse(_('No active categories'))

    photos_form = PhotosForm(request.POST, request.FILES)
    product_form = AddProductForm(request.POST or None) if 'name' in request.POST else AddProductForm()
    context = {
        'category_form': SelectCategoryProductForm(request.POST or None),
        'photos_form': photos_form,
        'product_form': product_form,}

    if request.method == 'POST':
        category_fields = {}
        if 'category' in request.POST:
            context['category'] = request.POST['category']
            category = Category.objects.get(id=context['category'])
            category_fields = get_category_fields(category=category)

        # creates a class (inherits from forms.Form class) with category_fields as attributes (form fields)
        CategoryFiltersForm = type('CategoryFiltersForm', (forms.Form,), category_fields)
        filters_form = CategoryFiltersForm(request.POST or None)
        context['filter_form'] = filters_form

        if all([filters_form.is_valid(), product_form.is_valid(),]):
            new_product = Product.objects.create(name=product_form.cleaned_data['name'],
                                                 description=product_form.cleaned_data['description'],
                                                 created_by = request.user, # default django user, probably will be switched to custom class later
                                                 category=category,
                                                 # tags, (added later in this view)
                                                 stock=product_form.cleaned_data['stock'],
                                                 photos=create_gallery(title=product_form.cleaned_data['name']),
                                                 attributes=filters_form.cleaned_data,
                                                 cost_price=product_form.cleaned_data['cost_price'],
                                                 selling_price=product_form.cleaned_data['selling_price'],
                                                 discount_percent=product_form.cleaned_data['discount_percent'],
                                                )
            # tags block
            new_product.tags.add(*product_form.cleaned_data['tags']) # using list as multiple positional arguments

            # new photos block
            if photos_form.is_valid():
                for image in request.FILES.getlist('photos'):
                    image_name = image.name + f'_{new_product.name}' # product's name is appended for later filtering purposes

                    # # this block wil be used in update view, not needed here
                    # if new_product.photos.photos.filter(title=image_name).exists(): # can't use get_or_create and have to specify slug because of some photologue bug
                    #     image_name += f'_{photo_models.Photo.objects.filter(title=image_name).count() + 1}'
                    # # this block wil be used in update view, not needed here

                    # TODO add any photologue filters down here
                    photo = photo_models.Photo.objects.create(image=image, title=image_name, slug=slugify(image_name)) #
                    new_product.photos.photos.add(photo)
            else:
                return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos (or photos form)'})}")
            return redirect('add_product')
    return render(request, "add_product.html", context)

@user_is_staff_or_404()
@require_http_methods(["GET", "POST"])
def edit_product_dynamic_view(request, id):
    # TODO add comments and docstr
    # """ If all the input is valid creates Product instance, photologue.Gallery instance (title=Product.name + _gallery),
    # associates it with product created, and, if provided, associates uploaded images with the gallery.
    # Passes selected 'category' as a parameter to the template so it's not lost when submitting main form
    # (category selecting is done via separate form).
    # """
    product_instance = Product.objects.get(id=id)
    current_category = Category.objects.get(id=request.POST['category']) if request.method == 'POST' else product_instance.category
    product_instance_data = {'name': product_instance.name,
                             'description': product_instance.description,
                             'tags': ', '.join(list(product_instance.tags.names())),
                             'stock': product_instance.stock,
                             'cost_price': product_instance.cost_price,
                             'selling_price': product_instance.selling_price,
                             'discount_percent': product_instance.discount_percent,}
    category_fields = get_category_fields(category=current_category)

    photos_display_urls = [ photo.get_display_url() for photo in product_instance.photos.photos.all() ]
    photos_form = PhotosForm(request.POST, request.FILES)
    product_form = AddProductForm(initial=product_instance_data)
    CategoryFiltersForm = type('CategoryFiltersForm', (forms.Form,), category_fields) # creates a class (inherits from forms.Form class) with category_fields as attributes (form fields)
    filters_form = CategoryFiltersForm(initial=product_instance.attributes)
    context = {
        'category_form': SelectCategoryProductForm(initial={'category': current_category}),
        'photos_form': photos_form,
        'product_form': product_form,
        'filter_form': filters_form,
        'product': product_instance,
        'photos_display_urls': photos_display_urls,
        'category': current_category.id,
        }

    if request.method == 'POST':
        if len(request.POST) > 2:
            product_form = AddProductForm(request.POST or None)
            filters_form = CategoryFiltersForm(request.POST or None)

        if all([filters_form.is_valid(), product_form.is_valid_check_same_name(current_name=product_instance.name),]):
            # here queryset.update() is not used because save() method is needed and foreign key field (category) doesn't get saved with bulk __dict__.update method
            # main edit block
            product_instance.name = product_form.cleaned_data['name']
            product_instance.category = current_category
            product_instance.description = product_form.cleaned_data['description']
            # tags, (added later in this view)
            # product_instance.photos: title ans slug of the gallery (and all its photos) are updated via product's save() method,
            product_instance.stock = product_form.cleaned_data['stock']
            product_instance.attributes = filters_form.cleaned_data
            product_instance.cost_price = product_form.cleaned_data['cost_price']
            product_instance.selling_price = product_form.cleaned_data['selling_price']
            product_instance.discount_percent = product_form.cleaned_data['discount_percent']

            product_instance.save(force_update=True)

            # tags block
            product_instance.tags.clear()
            product_instance.tags.add(*product_form.cleaned_data['tags']) # using list as multiple positional arguments

            # new photos block
            if photos_form.is_valid():
                for image in request.FILES.getlist('photos'):
                    image_name = image.name + f'_{product_instance.name}' # product's name is appended for later filtering purposes
                    if product_instance.photos.photos.filter(title=image_name).exists(): # can't use get_or_create and have to specify slug because of some photologue bug
                        image_name += f'_{photo_models.Photo.objects.filter(title__startswith=image_name).count() + 1}'
                    # TODO add any photologue filters down here
                    photo = photo_models.Photo.objects.create(image=image, title=image_name, slug=slugify(image_name)) #
                    product_instance.photos.photos.add(photo)
            else:
                return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos (or photos form)'})}")

            # current photos block
            for param_name in request.POST:
                # each photo_to_delete sends a POST parametr with the name "to_del_photo_{{ .get_display_url() }}"
                # E.g. "to_del_photo_/media/photologue/photos/cache/ImageName_rndnumbers_display.jpg"
                if param_name.startswith('to_del_photo_'):
                    # parse parameter name to get a substring of photo's image's name
                    # E.g. "ImageName_rndnumbers.jpg"
                    to_del_photo_image = str(param_name).replace('_display', '').split('/')[-1]
                    to_del_photo = product_instance.photos.photos.filter(image__endswith = to_del_photo_image)
                    # to_del_photo is a queryset, if delete() is run on it, the associated files won't be deleted
                    if to_del_photo.count() == 1:
                        # so it's run on the only instance of the queryset
                        to_del_photo.first().delete()
                    else:
                        return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos-to-delete number (not 1'})}")


            return redirect('edit_product', id=product_instance.id)
    return render(request, "edit_product.html", context)

class ProductsView(ListView):
    http_method_names = ['get', ]
    model = Product
    queryset = model.objects.filter(is_active=True)
    ordering = '-modified'
    paginate_by = 8
    template_name = 'products.html'
    context_object_name = 'products'
