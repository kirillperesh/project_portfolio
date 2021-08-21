from logging import raiseExceptions
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django import forms
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from urllib.parse import urlencode
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.views.generic.base import RedirectView
from proj_folio.defaults import DEFAULT_NO_IMAGE_URL

from photologue import models as photo_models
from .forms import AddProductForm, PhotosForm, SelectCategoryProductForm, RegisterForm, SignInForm
from .models import Category, Order, OrderLine, Product
from .decorators_mixins import user_is_staff_or_404, UserIsStaff_Or404_Mixin


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
                    # TODO Add some kind of validation here to select the right input field
                    category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},),
                                                                                          label=_(str(filter).capitalize()))
    return category_fields

def get_photo_image_name_from_img_src(img_src, exclude = '_display'):
    """Parses img_src gotten from photologue's .get_display_url() (or thumbnail)
    (E.g. "to_del_photo_/media/photologue/photos/cache/ImageName_rndnumbers_display.jpg")
    and returns a substring of photo's image's name. (E.g. "ImageName_rndnumbers.jpg)
    Excludes '_display' substring by default.
    """
    return str(img_src).replace(str(exclude), '').split('/')[-1]

def get_photo_from_img_src(*, img_src, model_instance, exclude = '_display'):
    """Returns a photo instance from product_instance.photos based on get_display_url() (or thumbnail)"""
    photo_image_substr = get_photo_image_name_from_img_src(img_src, exclude=exclude)
    photo_queryset = model_instance.photos.photos.filter(image__endswith = photo_image_substr)
    if photo_queryset.count() == 1: return photo_queryset.first()

def get_order(request, *, status, order_by='-created'):
    """Checks if there is an order of passed status, redirects to error 500 if not
    status: status str as stated in model definition
    order_by: generic django's ordering variable [default='-created']"""
    if not request.user.orders.filter(status=status).exists(): # check if there is a 'current' order
        return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'order (probably there is none)'})}")
    return request.user.orders.filter(status=status).order_by(order_by).first()

@user_is_staff_or_404()
@require_http_methods(["GET", "POST"])
def add_product_dynamic_view(request):
    """ If all the input is valid creates a Product instance, photologue.Gallery instance (title=Product.name + _gallery),
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
                    # TODO add any photologue filters down here
                    photo = photo_models.Photo.objects.create(image=image, title=image_name, slug=slugify(image_name)) #
                    new_product.photos.photos.add(photo)
            else:
                return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos (or photos form)'})}")
            # success
            new_product.save()
            return redirect('add_product')
    return render(request, "add_product.html", context)

@user_is_staff_or_404()
@require_http_methods(["GET", "POST"])
def edit_product_dynamic_view(request, id):
    """If all the input is valid edits a Product instance.
    If the name has changed, the gallery and all the photos get renamed as well.
    If a photo instance is removed, its associated files get deleted as well.
    """
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
        # if category is not the only POST arameter
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
            # tags block
            product_instance.tags.clear()
            product_instance.tags.add(*product_form.cleaned_data['tags']) # using list as multiple positional arguments
            # new photos block
            if photos_form.is_valid():
                for image in request.FILES.getlist('photos'):
                    image_name = image.name + f'_{product_instance.name}' # product's name is appended for later filtering purposes
                    if product_instance.photos.photos.filter(title=image_name).exists(): # can't use get_or_create and have to specify slug because of some photologue bug
                        image_name += f'_{photo_models.Photo.objects.filter(title__startswith=image_name).count() + 1}'
                    # TODO (or not) add any photologue filters down here
                    photo = photo_models.Photo.objects.create(image=image, title=image_name, slug=slugify(image_name)) #
                    product_instance.photos.photos.add(photo)
            else:
                return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos (or photos form)'})}")
            # current photos block
            for param_name in request.POST:
                if param_name.startswith('to_del_photo_'):
                    # get a photo instance from product_instance.photos based on get_display_url()
                    to_del_photo = get_photo_from_img_src(img_src=param_name,
                                                          model_instance=product_instance)
                    if to_del_photo:
                        to_del_photo.delete()
                    else:
                        return redirect(f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'photos-to-delete number (not 1)'})}")
            # update main_photo
            if 'new_main_photo' in request.POST:
                # get a photo instance from product_instance.photos based on get_display_url()
                new_main_photo = get_photo_from_img_src(img_src=request.POST['new_main_photo'],
                                                        model_instance=product_instance)
                if new_main_photo: product_instance.main_photo = new_main_photo
            # success
            # saving an instance here
            product_instance.save(force_update=True)
            return redirect('product_details', id=product_instance.id)
            # return redirect('products')
    return render(request, "edit_product.html", context)

@user_is_staff_or_404()
@require_http_methods(["GET",])
def delete_product_view(request, id):
    """Switches is_active status of a product.
    If 'recover' parameter is passed, is_active switches to True,
    else - False"""
    product_to_delete = get_object_or_404(Product, id=id)
    initial_status = product_to_delete.is_active
    product_to_delete.is_active = True if request.GET.__contains__('recover') else False
    product_to_delete.save()
    redirect_url = f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'product deletion (status has not change)'})}" if initial_status == product_to_delete.is_active else reverse('products')
    return redirect(redirect_url)

class ProductsView(ListView):
    http_method_names = ['get', ]
    model = Product
    # queryset = model.objects.filter(is_active=True)
    # ordering = '-modified'
    paginate_by = 9
    template_name = 'products.html'
    context_object_name = 'products'
    extra_context = {'no_image_url': DEFAULT_NO_IMAGE_URL}

    def get_queryset(self):
        queryset = self.model.objects.filter(is_active=True).order_by('-discount_percent', '-stock') # basic queryset
        # category filter block
        if self.request.GET.get('category'):
            category_filter = self.request.GET.get('category')
            queryset = queryset.filter(category__name=category_filter)
        # only_tag filter block
        if self.request.GET.get('only_tag'):
            only_tag_filter = self.request.GET.get('only_tag')
            queryset = queryset.filter(tags__name=only_tag_filter)
        return queryset

class ProductsStaffView(UserIsStaff_Or404_Mixin, ListView):
    # Paginating, ordering and filtering are done by JS DataTables
    http_method_names = ['get', ]
    model = Product
    queryset = model.objects.all()
    template_name = 'products_staff.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    http_method_names = ['get', ]
    model = Product
    pk_url_kwarg = 'id'
    queryset = model.objects.filter(is_active=True) # if product isn't active returns 404
    template_name = 'product.html'
    context_object_name = 'product'
    extra_context={'no_image_url': DEFAULT_NO_IMAGE_URL}

class Home(TemplateView):
    http_method_names = ['get', ]
    template_name = 'home.html'

class SignUpView(CreateView):
    http_method_names = ['get', 'post']
    model = User
    form_class = RegisterForm
    template_name = 'sign_up.html'

class SignInView(LoginView):
    http_method_names = ['get', 'post']
    authentication_form = SignInForm
    template_name = 'sign_in.html'

@login_required()
@require_http_methods(["GET", "POST"])
def cart_view(request):
    """
    TODO"""
    current_order = get_order(request, status='CUR') # select the latest current order
    if isinstance(current_order, HttpResponseRedirect): return current_order # return 500 if there is no current order
    if request.method=='POST':
        products_id_set = set(request.POST.getlist('products_id'))

        for order_line in current_order.order_lines.all(): # ordered by line_number by default
            if str(order_line.product.id) in products_id_set:
                quantity_list = request.POST.getlist(f'quantity_{order_line.product.id}')
                if len(quantity_list) > 1: # avoid duplicating
                    new_quantity = sum([int(num) for num in quantity_list])
                else:
                    new_quantity = int(quantity_list[0])
                if order_line.quantity != new_quantity:
                    order_line.quantity = new_quantity
                    order_line.save()
            else:
                order_line.delete()
    context = {}
    context['order'] = current_order
    context['order_lines'] = current_order.order_lines.all()
    return render(request, "cart.html", context)

class AddToCartView(LoginRequiredMixin, RedirectView):
    """Creates a new OrderLine of product given or increments an existing one
    If there's none, a current_order is created via user_logs_in signal"""
    http_method_names = ['post',]
    query_string = False

    def dispatch(self, request, *args, **kwargs):
        # from LoginRequiredMixin.dispatch
        if not request.user.is_authenticated: return self.handle_no_permission()
        # from RedirectView.dispatch
        if not request.method.lower() in self.http_method_names: return self.http_method_not_allowed(request, *args, **kwargs)
        current_order = get_order(request, status='CUR') # checks if there is and selects the latest current order
        if isinstance(current_order, HttpResponseRedirect): return current_order # return 500 if there is no current order
        self.url = request.POST.get('next', '/') # set redirect url
        product_id = request.POST.get('product_id')
        OrderLine.objects.create(parent_order=current_order,
                                 product=Product.objects.get(id=product_id),
                                 )
        return RedirectView.dispatch(self, request, *args, **kwargs)

@login_required()
@require_http_methods(["GET",])
def clear_cart_view(request, id):
    """Clears an order (deletes all its order_line)
    Also checks if the user has the permission (order instance belongs to the user or is_staff)"""
    order_to_clear = get_object_or_404(Order, id=id)
    # check user permissions to clear this cart
    if not (request.user.is_staff or order_to_clear.customer == request.user): raise Http404
    for order_line in order_to_clear.order_lines.all():
        order_line.delete()
    redirect_url = f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'cart (tried to clear it, but it did not become empty)'})}" if order_to_clear.order_lines.exists() else reverse('products')
    return redirect(redirect_url)





# TODO finish and docstr and comment cart_view
# TODO add lacking tests