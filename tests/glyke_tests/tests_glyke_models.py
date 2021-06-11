from django.db.models.signals import pre_delete
from django.test import TestCase, SimpleTestCase, Client, TransactionTestCase, tag
from django.urls import reverse, resolvers
from django.conf import settings
import importlib
import types, os
from unittest.mock import MagicMock
from django.apps import apps

from glyke_back.models import *
from glyke_back import signals


class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent_cat = Category.objects.get_or_create(name='Parent cat')[0]
        cls.sub_parent_cat = Category.objects.get_or_create(name='Sub-parent cat', parent = cls.parent_cat)[0]
        cls.child_cat = Category.objects.get_or_create(name='Child cat', parent = cls.sub_parent_cat)[0]
        cls.product_sub_parent = Product.objects.get_or_create(name='Product of sub-parent cat', category = cls.sub_parent_cat)[0]
        cls.product_child = Product.objects.get_or_create(name='Product of child cat', category = cls.child_cat)[0]

        cls.check = Check.objects.get_or_create(number=1, customer=None)[0]
        cls.check_line = CheckLine.objects.get_or_create(parent_check=cls.check, product=cls.product_child)[0]

    def test_pre_delete_signals(self, instance_list=[]):
        """Assert pre_delete signals are sent with proper arguments"""
        instance_list = [self.parent_cat, self.sub_parent_cat, self.child_cat, self.product_sub_parent, self.product_child]
        for instance in reversed(instance_list):
            handler = MagicMock() # Create handler
            signals.pre_delete.connect(handler, sender=instance.__class__)
            instance.delete()
            instance.save()
            # Assert the signal was called only once with the args
            handler.assert_called_once_with(signal=signals.pre_delete,
                                            sender=instance.__class__,
                                            instance = instance,
                                            using='default')

    def test_switch_parent_category_on_delete(self):
        """Assert categories of child categories and products switch to its 'grandparents'"""
        self.sub_parent_cat.delete()
        self.child_cat.refresh_from_db() # child category of sub_parent
        self.product_sub_parent.refresh_from_db() # child product of sub_parent
        self.assertEqual(self.child_cat.parent, self.sub_parent_cat.parent)
        self.assertEqual(self.product_sub_parent.category, self.sub_parent_cat.parent)

    def test_set_parent_category_none_on_delete(self):
        """Assert categories of child categories and products set to None if no parents available"""
        self.parent_cat.delete()
        Category.objects.get(name='Sub-parent cat').delete()
        self.child_cat.refresh_from_db() # child category of sub_parent
        self.product_sub_parent.refresh_from_db() # child product of sub_parent
        self.assertIsNone(self.child_cat.parent)
        self.assertIsNone(self.product_sub_parent.category)

    def test_get_deleted_instance_on_delete(self):
        """Assert a deleted instance is created on_delete"""
        self.product_child.delete()
        self.check_line.refresh_from_db()
        deleted_product_auto = Product.objects.get(name='_deleted_')
        self.assertEqual(self.check_line.product, deleted_product_auto)

    def test_is_active_switch(self):
        model_list = apps.get_models()
        for model in model_list:
            if hasattr(model, 'is_active'):
                model.objects.filter(is_active=True).update(is_active=False)
                self.assertFalse(model.objects.filter(is_active=True))











#  def test_on_delete_signals(self):
#         """Assert signal is sent with proper arguments"""

#         # Create handler
#         handler = MagicMock()
#         signals.pre_delete.connect(handler, sender=Category)

#         # Post the form or do what it takes to send the signal
#         # signals.pre_delete.send(sender=Category, instance = self.parent_cat, using='default')

#         self.parent_cat.delete()

#         # Assert the signal was called only once with the args
#         handler.assert_called_once_with(signal=signals.pre_delete, sender=Category, instance = self.parent_cat, using='default')

#         self.assertIsNone(self.sub_parent_cat.parent)