from os import name
from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_delete, post_delete, post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderLine


# when a category is deleted, switchs its children's parent attr to its own parent (or None)
@receiver(pre_delete,
          sender=Category,
          dispatch_uid='delete_category')
def category_pre_delete_handler(sender, instance, **kwargs):
    new_parent = instance.parent if instance.parent else None
    Category.objects.filter(parent_id=instance.id).update(parent=new_parent)
    Product.objects.filter(category_id=instance.id).update(category=new_parent)

# when an OrderLine is saved, its parent Order has to be updated
@receiver(post_save,
          sender=OrderLine,
          dispatch_uid='save_order_line')
def order_line_post_save_handler(sender, instance, **kwargs):
    instance.parent_order.save()

# when an OrderLine is deleted, its parent Order has to be updated
@receiver(post_delete,
          sender=OrderLine,
          dispatch_uid='delete_order_line')
def order_line_post_delete_handler(sender, instance, **kwargs):
    instance.parent_order.save()


# @receiver(user_logged_in,
#           sender=User,
#           dispatch_uid='user_logs_in')
# def user_logs_in_handler(sender, request, user, **kwargs):
#     if not user.orders.all().exists():
#         Order.objects.create(customer=user)

#     user_orders = user.orders.all()
#     current_order = user_orders.first()



#     print(user_orders)
#     print(current_order)
#     print(current_order.order_lines.all())

