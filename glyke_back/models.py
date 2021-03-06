import os
from django.db import models
from django.utils import timezone, dateformat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from urllib.error import HTTPError as HTTPError_fail_to_open_img
from model_utils.models import TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from proj_folio.settings import MEDIA_ROOT

from photologue import models as photo_models
from .managers import OrderFiltersManager


def get_deleted_instance(model):
    """Returns a callable to get a deleted instance of given model.
    Meant to be used as an argument for on_delete.SET().
    example: on_delete=models.SET(get_deleted_instance(Product))
    Also adds a description and a tag if the model has such attributes."""
    global get_deleted_instance_decorated
    def get_deleted_instance_decorated():
        deleted_instance, created = model.objects.get_or_create(name='_deleted_')
        if created:
            if hasattr(deleted_instance, 'description'):
                deleted_instance.description = f'Deleted {model.__name__.lower()}'
            if hasattr(deleted_instance, 'tags'):
                deleted_instance.tags.add('_deleted_')
            deleted_instance.save()
        return deleted_instance
    return get_deleted_instance_decorated

def get_upload_dir(base_dir, no_file_name=''):
    """Returns a callable to get a file path, using base_dir as root.
    Meant to be used as an upload_to argument of models.FileField.
    Returns file path of no_file_name if provided.
    example: default = get_upload_dir('category', no_file_name='no_image.png'),
             upload_to = get_upload_dir('category')"""
    if no_file_name: return f'{base_dir.lower()}/{no_file_name}'
    global get_upload_dir_decorated
    def get_upload_dir_decorated(instance, filename):
        name = slugify(instance.name.lower())
        return f'{base_dir.lower()}/{name}/{filename}'
    return get_upload_dir_decorated


class Category(TimeStampedModel):
    __original_name = None # an attribute to keep track on the previous name when changed
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), max_length=1000, blank=True)
    parent = models.ForeignKey('self',
                               on_delete=models.DO_NOTHING, # switches to category's parent or null. handled via Category's pre_delete signal
                               verbose_name=_('parent'),
                               related_name='child_categories',
                               blank=True,
                               null=True)
    child_level = models.IntegerField(_('child level'),
                                      validators=[MinValueValidator(0)],
                                      default=0) # 0 level is top_lvl_category
    ordering_index = models.IntegerField(_('ordering index'), # ordering index for templates' select options
                                      validators=[MinValueValidator(1)],
                                      blank=True,
                                      null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    picture = models.ImageField(_('picture'),
                                default = get_upload_dir('category', no_file_name='no_image.png'),
                                upload_to = get_upload_dir('category'),
                                max_length = 255)
    filters = TaggableManager(verbose_name=_('filters'),
                              help_text=_("A comma-separated list of atrributes"),
                              blank=True)
    bg_color = models.CharField(_('background color'),
                                max_length=50,
                                blank=True,
                                null=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["ordering_index",]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        """__init__ is overridden to track self.name changes"""
        super().__init__(*args, **kwargs)
        self.__original_name = self.name

    def save(self, *args, **kwargs):
        """Updates child_level based on how many ancestor "levels" does the current instance have.
        Ordering_index is used for sorting in templates (basically categories are numerated top down as if they were in a fully unrolled list 1 -> 1.1 -> 1.2 -> 1.2.1 -> 1.3 -> 2)
        Update instance's ordering_index aftercalling super().save()"""
        just_created = False if self.pk else True
        # child_level block
        self.child_level = 0 # top-lvl-categories are 0
        current_parent = self.parent
        while True:
            if not current_parent: break
            self.child_level += 1
            current_parent = current_parent.parent
        super().save(*args, **kwargs)

        # ordering_index block
        if just_created or self.name != self.__original_name: # update all ordering_indices if a new category was created or any category got renamed
            indiced_order_by = 'name' # basic ordering for ordering_indices
            self.next_index = 1 # starting from 1
            def numerate_category_recur(current_parrent_cat):
                if current_parrent_cat.ordering_index != self.next_index:
                    # do not disturb the DB if an instance's ordering_index doesn't have to be updated
                    current_parrent_cat.ordering_index = self.next_index
                    current_parrent_cat.save()
                self.next_index += 1
                if current_parrent_cat.child_categories.exists():
                    for child_category in current_parrent_cat.child_categories.order_by(indiced_order_by):
                        numerate_category_recur(child_category)

            # start from top-lvl-categories and proceed recursively through all their children
            for parent_category in Category.objects.filter(parent__isnull=True).order_by(indiced_order_by):
                numerate_category_recur(parent_category)

class Price(models.Model):
    cost_price = models.DecimalField(_('cost price'),
                                     max_digits=7,
                                     decimal_places=2,
                                     validators=[MinValueValidator(0)],
                                     default=0)
    selling_price = models.DecimalField(_('selling price'),
                                        max_digits=7,
                                        decimal_places=2,
                                        validators=[MinValueValidator(0)],
                                        default=0)
    discount_percent = models.IntegerField(_('discount, %'),
                                           validators=[MinValueValidator(0),
                                           MaxValueValidator(80)],
                                           default=0)
    end_user_price = models.DecimalField(_('end user price'),
                                         max_digits=7,
                                         decimal_places=2,
                                         validators=[MinValueValidator(0)],
                                         default=0)
    profit = models.DecimalField(_('profit'), max_digits=7, decimal_places=2, default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # recount profit and end_user_price on save
        self.end_user_price = self.selling_price * Decimal(1 - self.discount_percent / 100)
        self.end_user_price = Decimal(self.end_user_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.profit = self.end_user_price - self.cost_price
        super().save(*args, **kwargs)

class Product(Price, TimeStampedModel):
    __original_name = None # an attribute to keep track on the previous name when changed
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), max_length=3000, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category,
                                 on_delete=models.DO_NOTHING, # switches to category's parent or null. handled via Category's pre_delete signal
                                 verbose_name=_('category'),
                                 related_name='products',
                                 blank=True,
                                 null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    tags = TaggableManager()
    stock = models.IntegerField(_('stock'), validators=[MinValueValidator(0)], default=0)
    photos = models.OneToOneField(photo_models.Gallery,
                                  on_delete=models.SET_NULL,
                                  verbose_name=_('photos'),
                                  blank=True,
                                  null=True)
    main_photo = models.OneToOneField(photo_models.Photo, # Product's main photo, is chosen from its current photos
                                      on_delete=models.SET_NULL,
                                      verbose_name=_('main photo'),
                                      blank=True,
                                      null=True)
    attributes = models.JSONField(_('attributes'), blank = True, null=True)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        """__init__ is overridden to track self.name changes"""
        super().__init__(*args, **kwargs)
        self.__original_name = self.name

    def save(self, *args, **kwargs):
        # main_photo block: update main_photo
        try:# check if main_photo is None or has just been deleted (DoesNotExist is raised)
            if not self.main_photo: raise photo_models.Photo.DoesNotExist
        except photo_models.Photo.DoesNotExist:
            if self.photos: self.main_photo = self.photos.photos.all().first() # sets main_photo to default value (first() for now)
        # name's changed block: change galery's and photos' names if the product got renamed
        if self.name != self.__original_name:
            self.photos.title = self.name + _("_gallery")
            self.photos.slug = slugify(self.name + _("_gallery"))
            for photo in self.photos.photos.all():
                photo.title = str(photo.title).replace(self.__original_name, self.name)
                photo.slug = str(photo.slug).replace(slugify(self.__original_name), slugify(self.name))
                photo.save()
            self.photos.save()
        # status block: products with no selling price cannot be shown or added to cart, therefor should be marked as inactive
        if self.selling_price <= 0: self.is_active = False
        super().save(*args, **kwargs)
        self.__original_name = self.name

    def add_images_from_url(self, *, url_list):
        """Saves images from url_list to photologue/photos folder, then creates photologue photo instances of them and assignes them to the current product instance"""
        for url in url_list:
            img_extention = f".{str(url).split('.')[-1]}"
            temp_img = NamedTemporaryFile(suffix=img_extention, dir=os.path.join(MEDIA_ROOT, 'photologue', 'photos'))
            try:
                with urlopen(url) as uo:
                    if uo.status != 200: continue
                    temp_img.write(uo.read())
                    temp_img.flush()
            except HTTPError_fail_to_open_img: continue # skips an image if it failed to open
            image_file = File(temp_img)
            image_name = f"{get_random_string(length=5)}_{str(url).split('/')[-1][-10:]}_{self.name}"
            photo = photo_models.Photo.objects.create(image=image_file, title=image_name, slug=slugify(image_name))
            self.photos.photos.add(photo)

class Order(Price, TimeStampedModel):
    """Prices represent the total value of an order
    Discount is removed"""
    objects = OrderFiltersManager() # this manager adds get_latest_current method, which is needed for the order_panel template

    CURRENT_ORDER = 'CUR'
    PENDING = 'PEN'
    CONFIRMED = 'CON'
    DELIVERING = 'DNG'
    DELIVERED = 'DED'
    COMPLETED = 'COM'
    ARCHIVED = 'ARC'
    CANCELED = 'CAN'
    ORDER_STATUS_CHOICES = [
        (CURRENT_ORDER, 'Current order'),
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (DELIVERING, 'Delivering'),
        (DELIVERED, 'Delivered'),
        (COMPLETED, 'Completed'),
        (ARCHIVED, 'Archived'),
        (CANCELED, 'Canceled'),
    ]
    status = models.CharField(max_length=3,
                              choices=ORDER_STATUS_CHOICES,
                              default=CANCELED,
                              )
    discount_percent = None # inherited from Price, but no need for it for the Order model
    number = models.CharField(_('number'), max_length=100, blank=True)
    customer = models.ForeignKey(User,
                                 on_delete=models.SET_NULL,
                                 verbose_name=_('customer'),
                                 related_name='orders',
                                 blank=False,
                                 null=True)
    items_total = models.IntegerField(_('items total'), validators=[MinValueValidator(0)], default=0)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        name = self.customer.username if self.customer else 'no_name'
        return f"{self.created.strftime('%H:%M:%S %d.%m.%y')} | {name}"

    def save(self, *args, **kwargs):
        # generate order's number on creation
        if not self.pk:
            name_time_stamp = dateformat.format(timezone.localtime(timezone.now()), 'His_dmy')
            prefix = self.customer.username[:5] if self.customer else 'no_name'
            self.number = f'{prefix}_{name_time_stamp}'

        order_prices_sum = self.order_lines.all().aggregate(models.Sum('cost_price'), models.Sum('end_user_price'), models.Sum('selling_price'))
        self.cost_price = Decimal(order_prices_sum['cost_price__sum']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if order_prices_sum['cost_price__sum'] else 0
        self.end_user_price = Decimal(order_prices_sum['end_user_price__sum']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if order_prices_sum['end_user_price__sum'] else 0
        self.selling_price = Decimal(order_prices_sum['selling_price__sum']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if order_prices_sum['selling_price__sum'] else 0
        self.profit = self.end_user_price - self.cost_price

        items_sum = self.order_lines.all().aggregate(models.Sum('quantity'))
        self.items_total = items_sum['quantity__sum'] if items_sum['quantity__sum'] else 0

        TimeStampedModel.save(self, *args, **kwargs) # not calling super() here because the logic of price recounting for the Order model is different

class OrderLine(Price):
    """Prices represent the aggregate value for a line (product.price * quantity)
    Discount stays untouched"""
    parent_order = models.ForeignKey(Order,
                                     on_delete=models.CASCADE,
                                     verbose_name=_('order'),
                                     related_name='order_lines',
                                     blank=False)
    line_number = models.PositiveIntegerField(_('line number'), blank=True)
    product = models.ForeignKey(Product,
                                on_delete=models.SET(get_deleted_instance(Product)),
                                verbose_name=_('product'),
                                related_name='order_lines',
                                blank=False)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)

    class Meta:
        ordering = ['line_number']

    def __str__(self):
        return f'{self.parent_order} | Line: {self.line_number}'

    def save(self, *args, **kwargs):
        if not self.pk: # on creation
            # numerate the line
            lines_count = self.parent_order.order_lines.count()
            self.line_number = (lines_count + 1) if lines_count else 1

        # avoid duplicating
        duplicating_line = self.parent_order.order_lines.filter(product=self.product).first()
        if duplicating_line and duplicating_line != self:
            # doesn't create a new instance if duplicate already exists (only increments duplicate's quantity)
            duplicating_line.quantity += self.quantity
            duplicating_line.save()
        else:
            # update prices on save()
            self.cost_price = self.product.cost_price * self.quantity
            self.selling_price = self.product.selling_price * self.quantity
            self.end_user_price = self.product.end_user_price * self.quantity
            self.discount_percent = self.product.discount_percent
            self.profit = self.end_user_price - self.cost_price

            models.Model.save(self, *args, **kwargs) # not calling super() here because the logic of price recounting for the Order model is different


# TODO add defaul no_image from defaults to category photo
# TODO if any category filter has been renamed or deleted, corresponding product attributes have to be renamed or delete either