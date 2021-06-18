from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
# from django.contrib.auth.decorators import user_passes_test
from django.utils.text import slugify

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

    from django.http import HttpResponse, HttpResponseRedirect
    return HttpResponseRedirect('%s?%s' % (reverse('smth_went_wrong'), {'error_suffix':'photos (or photos form)'}))
    return redirect('smth_went_wrong', error_suffix='photos (or photos form)')

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

            for filter in category.filters.all(): # these are django-taggit objects
                # TODO Add some king of validation here to select the right input field
                category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},),
                                                                                      label=_(str(filter).capitalize()))
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

            # photos block
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
                # TODO add this url and view
                return redirect('smth_went_wrong', error_suffix='photos (or photos form)')

            # TODO add redirect on success
    return render(request, "add_product.html", context)

