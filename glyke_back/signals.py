from logging import raiseExceptions
from os import name
from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_delete, post_delete, post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderLine


@receiver(pre_delete,
          sender=Category,
          dispatch_uid='delete_category')
def category_pre_delete_handler(sender, instance, **kwargs):
    """When a category is deleted, switchs its children's parent attr to its own parent (or None)"""
    new_parent = instance.parent if instance.parent else None
    sender.objects.filter(parent_id=instance.id).update(parent=new_parent)
    Product.objects.filter(category_id=instance.id).update(category=new_parent)

@receiver(post_save,
          sender=OrderLine,
          dispatch_uid='save_order_line')
def order_line_post_save_handler(sender, instance, **kwargs):
    """When an OrderLine is saved, its parent Order has to be updated"""
    instance.parent_order.save()

@receiver(post_delete,
          sender=OrderLine,
          dispatch_uid='delete_order_line')
def order_line_post_delete_handler(sender, instance, **kwargs):
    """When an OrderLine is deleted, its parent Order has to be updated"""
    instance.parent_order.save() # save parent_order to update its prices

@receiver(user_logged_in,
          sender=User,
          dispatch_uid='user_logs_in')
def user_logs_in_handler(sender, request, user, **kwargs):
    """Checks if there is a current_order, creates one if not"""
    if not user.orders.filter(status='CUR').exists():
        Order.objects.create(customer=user, status='CUR')

@receiver(post_save,
          sender=Order,
          dispatch_uid='save_order')
def order_post_save_handler(sender, instance, **kwargs):
    """When an Order is saved, its lines' numbers have to be updated"""
    for order_line in instance.order_lines.all(): # update order_line line_numbers (order by line_number)
        while True:
            if order_line.line_number == 1 or instance.order_lines.filter(line_number=order_line.line_number-1).exists():
                break
            else:
                instance.order_lines.filter(id=order_line.id).update(line_number=order_line.line_number-1)