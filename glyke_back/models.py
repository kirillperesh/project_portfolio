import os
import re
from django.db import models
from django.db.models.deletion import SET_NULL
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django.contrib.auth.models import User


def get_deleted_instance(model):
    global get_deleted_instance_decorated
    def get_deleted_instance_decorated():
        deleted_instance = model.objects.get_or_create(name='_deleted_', description=f'Deleted {model.__name__}')[0]
        deleted_instance.tags.add('_deleted_')
        return deleted_instance
    return get_deleted_instance_decorated

def get_category_upload_dir(instance, filename):
    return f'categories/{instance.name}/{filename}'



class Category(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1000, blank=True)

    # TODO and post_delete signal for this thing to switch category to next parent or unknown one https://stackoverflow.com/questions/43857902/django-set-foreign-key-to-parent-value-on-delete
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='child_categories', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    picture = models.ImageField(default = f'categories/no_image.png', upload_to = get_category_upload_dir, max_length = 255)

    def __str__(self) -> str:
        return self.name

class Price(models.Model):
    cost_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    discount_percent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(80)], default=0)
    profit = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        abstract = True

class Product(Price, TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=3000, blank=True)

    # TODO and post_delete signal for this thing to switch category to next parent or unknown one https://stackoverflow.com/questions/43857902/django-set-foreign-key-to-parent-value-on-delete
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='products', blank=False, null=True)
    tags = TaggableManager()
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    # TODO pictures

    def __str__(self) -> str:
        return self.name

class Check(Price, TimeStampedModel):
    number = models.CharField(max_length=100, null=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='checks', blank=False, null=True)





class CheckLine(Price):
    parent_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name='check_lines', blank=False)
    line_number = models.PositiveIntegerField(default=1)
    product = models.ForeignKey(Product, on_delete=models.SET(get_deleted_instance(Product)), related_name='check_lines', blank=False)
    quantity = models.PositiveIntegerField(default=1)