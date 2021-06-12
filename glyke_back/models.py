from django.db import models
from django.db.models.deletion import SET_NULL
from django.db.models.expressions import F
from django.utils import timezone, dateformat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django.contrib.auth.models import User

from photologue import models as photo_models

def get_deleted_instance(model):
    """ADD"""
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

def get_upload_dir(base_dir, no_image_name=''):
    """ADD"""
    if no_image_name: return f'{base_dir.lower()}/{no_image_name}'
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
                                default = get_upload_dir('category', 'no_image.png'),
                                upload_to = get_upload_dir('category'),
                                max_length = 255)

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
    profit = models.DecimalField(_('profit'), max_digits=6, decimal_places=2, default=0)

    class Meta:
        abstract = True

class Product(Price, TimeStampedModel):
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), max_length=3000, blank=True)
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

    def __str__(self):
        return self.name

class Check(Price, TimeStampedModel):
    number = models.CharField(_('number'), max_length=100, blank=True)
    customer = models.ForeignKey(User,
                              on_delete=models.SET_NULL,
                              verbose_name=_('customer'),
                              related_name='checks',
                              blank=False,
                              null=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        name = self.customer.username if self.customer else 'no_name'
        return f"{self.created.strftime('%H:%M:%S %d.%m.%y')} | {name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            time_stamp = dateformat.format(timezone.localtime(timezone.now()), 'His_dmy')
            prefix = self.customer.username[:5] if self.customer else 'no_name'
            self.number = f'{prefix}_{time_stamp}'
        super(Check, self).save(*args, **kwargs)


class CheckLine(Price):
    parent_check = models.ForeignKey(Check,
                                     on_delete=models.CASCADE,
                                     verbose_name=_('check'),
                                     related_name='check_lines',
                                     blank=False)
    line_number = models.PositiveIntegerField(_('line number'), blank=True)
    product = models.ForeignKey(Product,
                                on_delete=models.SET(get_deleted_instance(Product)),
                                verbose_name=_('product'),
                                related_name='check_lines',
                                blank=False)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)

    def __str__(self):
        return f'{self.parent_check} | Line: {self.line_number}'

    def save(self, *args, **kwargs):
        if not self.pk:
            lines_count = self.parent_check.check_lines.count()
            self.line_number = (lines_count + 1) if lines_count else 1
        super(CheckLine, self).save(*args, **kwargs)


