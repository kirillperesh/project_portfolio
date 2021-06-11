from os import name
from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_delete, post_delete
from .models import Category, Product


# when a category is deleted, switchs its children's parent attr to its own parent (or None)
@receiver(pre_delete,
          sender=Category,
          dispatch_uid='delete_category')
def category_post_delete_handler(sender, instance, **kwargs):
    new_parent = instance.parent if instance.parent else None
    Category.objects.filter(parent_id=instance.id).update(parent=new_parent)
    Product.objects.filter(category_id=instance.id).update(category=new_parent)


