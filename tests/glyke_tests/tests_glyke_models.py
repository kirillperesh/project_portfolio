from django.test import TestCase
from unittest.mock import MagicMock
from django.apps import apps
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from glyke_back.models import *
from glyke_back import signals



class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_not_staff = User.objects.get_or_create(username='user_not_staff', password='password')[0]

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
        """Assert is_active attribute switches correctly"""
        model_list = apps.get_models()
        for model in model_list:
            if hasattr(model, 'is_active'):
                model.objects.all().update(is_active=False)
                self.assertFalse(model.objects.filter(is_active=True))
                model.objects.all().update(is_active=True)
                self.assertFalse(model.objects.filter(is_active=False))

    def test__str__methods(self):
        """Assert __str__ methods work properly"""
        rnd_str = get_random_string(length=10)
        category = Category.objects.create(name=rnd_str)
        self.assertEqual(str(category), rnd_str)
        product = Product.objects.create(name=rnd_str)
        self.assertEqual(str(product), rnd_str)
        check_no_user = Check.objects.create(number=rnd_str, customer=None)
        self.assertIn('no_name', str(check_no_user))
        check = Check.objects.create(number=rnd_str, customer=self.user_not_staff)
        self.assertIn(self.user_not_staff.username, str(check))
        checkline_no_user = CheckLine.objects.create(parent_check=check_no_user, product=product)
        self.assertIn('no_name | Line: 1', str(checkline_no_user))
        checkline = CheckLine.objects.create(parent_check=check, product=product)
        self.assertIn(f'{self.user_not_staff.username} | Line: 1', str(checkline))

    def test_checkline_autoinc(self):
        """Assert line auto-numering in checks work properly"""
        check_no_user = Check.objects.create(number=1, customer=None)
        checkline_1 = CheckLine.objects.create(parent_check=check_no_user, product=self.product_child)
        self.assertEqual(checkline_1.line_number, check_no_user.check_lines.count())
        checkline_2 = CheckLine.objects.create(parent_check=check_no_user, product=self.product_child)
        self.assertEqual(checkline_2.line_number, check_no_user.check_lines.count())

    # def test_auto_upload_dir_method(self):
    #     import tempfile
    #     self.assertEqual(str(self.parent_cat.picture), 'category/no_image.png')
    #     rnd_str = get_random_string(length=10)
    #     print(self.parent_cat.picture)
    #     self.parent_cat.picture = tempfile.NamedTemporaryFile(suffix=".jpg").name
    #     print(self.parent_cat.picture)
    #     self.parent_cat.save()
    #     print(self.parent_cat.picture)
    #     # self.parent_cat.picture = SimpleUploadedFile(name=rnd_str, content=open('./media', 'rb').read(), content_type='image/jpeg')

    #     from django.core.files import File
    #     file_mock = MagicMock(spec=File)
    #     self.parent_cat.picture = file_mock



    #     print(self.parent_cat.picture)











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