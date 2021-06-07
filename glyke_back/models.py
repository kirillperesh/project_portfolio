from django.db import models
from django.db.models.deletion import SET_NULL
from django.utils import timezone, dateformat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django.contrib.auth.models import User


def get_deleted_instance(model):
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

def get_upload_dir(base_dir):
    global get_upload_dir_decorated
    def get_upload_dir_decorated(instance, filename):
        name = slugify(instance.name.lower())
        return f'{base_dir.lower()}/{name}/{filename}'
    return get_upload_dir_decorated


class Category(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1000, blank=True)

    # TODO and post_delete signal for this thing to switch category to next parent or unknown one https://stackoverflow.com/questions/43857902/django-set-foreign-key-to-parent-value-on-delete
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='child_categories', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    picture = models.ImageField(default = f'category/no_image.png', upload_to = get_upload_dir('category'), max_length = 255)

    def __str__(self) -> str:
        return self.name

class Price(models.Model):
    cost_price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    selling_price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    discount_percent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(80)], default=0)
    profit = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        abstract = True

class Product(Price, TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=3000, blank=True)

    # TODO and post_delete signal for this thing to switch category to next parent or unknown one https://stackoverflow.com/questions/43857902/django-set-foreign-key-to-parent-value-on-delete
    category = models.ForeignKey(Category, on_delete=models.SET(get_deleted_instance(Category)), related_name='products', blank=False)
    tags = TaggableManager()
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    # TODO pictures

    def __str__(self) -> str:
        return self.name

class Check(Price, TimeStampedModel):
    number = models.CharField(max_length=100, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='checks', blank=False, null=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.created} | {self.buyer.username}'

    def save(self, *args, **kwargs):
        if not self.pk:
            time_stamp = dateformat.format(timezone.localtime(timezone.now()), 'His_dmy')
            self.number = f'{self.buyer.username[:5]}_{time_stamp}'
        super(Check, self).save(*args, **kwargs)


class CheckLine(Price):
    parent_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name='check_lines', blank=False)
    line_number = models.PositiveIntegerField(blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET(get_deleted_instance(Product)), related_name='check_lines', blank=False)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.parent_check} | Line: {self.line_number}'

    def save(self, *args, **kwargs):
        if not self.pk:
            lines_count = self.parent_check.check_lines.count()
            self.line_number = (lines_count + 1) if lines_count else 1
        super(CheckLine, self).save(*args, **kwargs)


