from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_delete, post_delete, post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderLine


def recur_update_child_categories_child_level(current_parrent, *, update_by):
    """Recursively updates all children's child_level by update_by value"""
    if current_parrent.child_categories.exists():
        new_child_level = current_parrent.child_categories.first().child_level + update_by
        current_parrent.child_categories.update(child_level=new_child_level)
        for child_category in current_parrent.child_categories.all():
            recur_update_child_categories_child_level(child_category, update_by=-1)

@receiver(pre_delete,
          sender=Category,
          dispatch_uid='pre_delete_category')
def category_pre_delete_handler(sender, instance, **kwargs):
    """When a category is deleted, switchs its children's parent attr to its own parent (or None).
    Also decrement all the following (by ordering_index after this instance) categories' ordering indices by 1.
    Also decrement all instance's children's child_level by 1."""
    instance.refresh_from_db() # because sometimes instance.ordering_index doesn't get updated
    for category in sender.objects.filter(ordering_index__gt=instance.ordering_index):
        category.ordering_index -= 1
        category.save()

    # decrement all children's child_level by 1
    # needs to be run after all Category.save() methods
    recur_update_child_categories_child_level(instance, update_by=-1)

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