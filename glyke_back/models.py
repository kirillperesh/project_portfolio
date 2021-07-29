from django.db import models
from django.utils import timezone, dateformat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP

from photologue import models as photo_models


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
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), max_length=1000, blank=True)
    parent = models.ForeignKey('self',
                               on_delete=models.DO_NOTHING, # switches to category's parent or null. handled via Category's pre_delete signal
                               verbose_name=_('parent'),
                               related_name='child_categories',
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

    def __str__(self):
        return self.name


class Price(models.Model):
    cost_price = models.DecimalField(_('cost price'),
                                     max_digits=6,
                                     decimal_places=2,
                                     validators=[MinValueValidator(0)],
                                     default=0)
    selling_price = models.DecimalField(_('selling price'),
                                        max_digits=6,
                                        decimal_places=2,
                                        validators=[MinValueValidator(0)],
                                        default=0)
    discount_percent = models.IntegerField(_('discount, %'),
                                           validators=[MinValueValidator(0),
                                           MaxValueValidator(80)],
                                           default=0)
    end_user_price = models.DecimalField(_('end user price'),
                                         max_digits=6,
                                         decimal_places=2,
                                         validators=[MinValueValidator(0)],
                                         default=0)
    profit = models.DecimalField(_('profit'), max_digits=6, decimal_places=2, default=0)

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
    main_photo = models.OneToOneField(photo_models.Photo, # TODO add comment
                                      on_delete=models.SET_NULL,
                                      verbose_name=_('main photo'),
                                      blank=True,
                                      null=True)
    attributes = models.JSONField(_('attributes'), blank = True, null=True)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_name = self.name

    def save(self, *args, **kwargs):
        # main_photo block: update main_photo
        try: # check if main_photo is None or has just been deleted (DoesNotExist is raised)
            if not self.main_photo: raise photo_models.Photo.DoesNotExist
        except photo_models.Photo.DoesNotExist:
            if self.photos: self.main_photo = self.photos.photos.all().first() # sets main_photo to default value (first() for now)
        # name's changed block: change galery's and photos' names if the product got renamed
        if self.name != self.__original_name:
            self.photos.title = self.name + _("_gallery")
            self.photos.slug = slugify(self.name + _("_gallery"))
            for photo in self.photos.photos.all():
                photo.title = str(photo.title).replace(self.__original_name, self.name)
                photo.slug = str(photo.slug).replace(self.__original_name, self.name)
                photo.save()
            self.photos.save()
        super().save(*args, **kwargs)
        self.__original_name = self.name

class Order(Price, TimeStampedModel):
    """Prices represent the total value for an order
    Discount is removed"""
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

        # update prices and items_total on save()
        order_prices_sum = self.order_lines.all().aggregate(models.Sum('cost_price'), models.Sum('end_user_price'), models.Sum('selling_price'))
        self.cost_price = order_prices_sum['cost_price__sum'] if order_prices_sum['cost_price__sum'] else 0
        self.end_user_price = order_prices_sum['end_user_price__sum'] if order_prices_sum['end_user_price__sum'] else 0
        self.selling_price = order_prices_sum['selling_price__sum'] if order_prices_sum['selling_price__sum'] else 0
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

    def __str__(self):
        return f'{self.parent_order} | Line: {self.line_number}'

    def save(self, *args, **kwargs):
        # numerate the line
        if not self.pk:
            lines_count = self.parent_order.order_lines.count()
            self.line_number = (lines_count + 1) if lines_count else 1
        # update prices on save()
        self.cost_price = self.product.cost_price * self.quantity
        self.selling_price = self.product.selling_price * self.quantity
        self.end_user_price = self.product.end_user_price * self.quantity
        self.discount_percent = self.product.discount_percent
        self.profit = self.end_user_price - self.cost_price

        models.Model.save(self, *args, **kwargs) # not calling super() here because the logic of price recounting for the Order model is different


# TODO add defaul no_image from defaults to category photo
# TODO if any category filter has been renamed or deleted, corresponding product attributes have to be renamed or delete either