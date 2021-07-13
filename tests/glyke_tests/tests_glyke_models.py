from django.test import TestCase, override_settings
from django.db.models.signals import pre_delete
from unittest.mock import MagicMock
from django.apps import apps
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile, shutil # temp dir to test filefields (test_auto_upload_dir_method)
from django.utils.text import slugify
import random
import decimal

from photologue import models as photo_models
from glyke_back.models import *
from glyke_back.views import create_gallery
from glyke_back import signals


def get_random_temp_file(extension):
    """"Creates a temporary byte file for testing purposes of given extension.
    Returns a tuple of (random file, name)"""
    rnd_file_name = f'{get_random_string(length=10)}.{str(extension)}'
    return (SimpleUploadedFile(rnd_file_name, b"these are the file contents"), rnd_file_name)



MEDIA_ROOT = tempfile.mkdtemp() # temp dir to test filefields (test_auto_upload_dir_method)
@override_settings(MEDIA_ROOT=MEDIA_ROOT) # temp dir to test filefields (test_auto_upload_dir_method)
class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_not_staff = User.objects.create(username='user_not_staff', password='password')

        cls.parent_cat = Category.objects.create(name='Parent cat')
        cls.sub_parent_cat = Category.objects.create(name='Sub-parent cat', parent = cls.parent_cat)
        cls.child_cat = Category.objects.create(name='Child cat', parent = cls.sub_parent_cat)
        cls.product_sub_parent = Product.objects.create(name='Product of sub-parent cat', category = cls.sub_parent_cat)
        cls.product_child = Product.objects.create(name='Product of child cat', category = cls.child_cat)

        cls.check = Check.objects.create(number=1, customer=None)
        cls.check_line = CheckLine.objects.create(parent_check=cls.check, product=cls.product_child)

    @classmethod
    def tearDownClass(cls):  # delete temp dir on teardown
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pre_delete_signals(self, instance_list=[]):
        """Assert pre_delete signals are sent with proper arguments"""
        instance_list = [self.parent_cat, self.sub_parent_cat, self.child_cat, self.product_sub_parent, self.product_child]
        for instance in reversed(instance_list):
            handler = MagicMock() # Create handler
            pre_delete.connect(handler, sender=instance.__class__)
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

    def test_auto_upload_dir_method(self):
        """Assert models.get_upload_dir function works properly"""
        # case: category w/o picture
        self.assertEqual(str(self.parent_cat.picture), 'category/no_image.png')
        # case: category w/ temporary random picture
        rnd_temp_file, rnd_temp_file_name = get_random_temp_file('jpg')
        self.parent_cat.picture = rnd_temp_file
        self.parent_cat.save()
        cat_name_slug = slugify(self.parent_cat.name.lower())
        self.assertEqual(str(self.parent_cat.picture), f'category/{cat_name_slug}/{rnd_temp_file_name}')

    def test_product_create_assign_photo(self):
        """Assert product save method assigns the main_photo attr on creation"""
        rnd_product_name = get_random_string(length=20)
        gallery = create_gallery(title=rnd_product_name)
        img_file, img_file_name = get_random_temp_file('jpg')
        photo = photo_models.Photo.objects.create(image=img_file, title=img_file_name, slug=slugify(img_file_name))
        gallery.photos.add(photo)
        product = Product.objects.create(name=rnd_product_name, photos=gallery)
        self.assertIsNotNone(product.photos)
        self.assertEqual(gallery.slug, slugify(product.name + "_gallery"))
        self.assertEqual(product.main_photo, photo)

    def test_product_save_profit_update(self):
        """Assert product save method updates profit attr"""
        def update_check_prices():
            product.cost_price = rnd_cost_price
            product.discount_percent = rnd_discount
            product.selling_price = rnd_selling_price
            product.save()
            test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)-rnd_cost_price).quantize(Decimal('0.01'))
            self.assertEqual(product.profit, test_profit)
            self.assertEqual(product.cost_price, rnd_cost_price)
            self.assertEqual(product.discount_percent, rnd_discount)
            self.assertEqual(product.selling_price, rnd_selling_price)
            self.assertEqual(product.profit, product.end_user_price-rnd_cost_price)
        # case: all 0
        product = Product.objects.create(name='test_product')
        self.assertEqual(product.profit, 0)
        # case: profit > 0, w/ discount
        rnd_cost_price = decimal.Decimal(random.randrange(1, 9999))/100
        rnd_selling_price = decimal.Decimal(random.randrange((rnd_cost_price*100), 9999))/100
        rnd_discount = random.randint(0, int((1-(rnd_cost_price/rnd_selling_price))*100))
        update_check_prices()
        self.assertGreaterEqual(product.profit, 0)
        # case: profit > 0, no discount
        rnd_discount = 0
        update_check_prices()
        self.assertGreaterEqual(product.profit, 0)
        # case: profit < 0, no discount
        rnd_selling_price = decimal.Decimal(random.randrange(1, 9999))/100
        rnd_cost_price = decimal.Decimal(random.randrange((rnd_selling_price*100), 9999))/100
        update_check_prices()
        self.assertLessEqual(product.profit, 0)
        # case: profit < 0, w/ discount
        rnd_discount = random.randint(1, 80)
        update_check_prices()

    def test_product_save_end_user_price_update(self):
        """Assert product save method updates end_user_price attr"""
        def update_check_prices():
            product.discount_percent = rnd_discount
            product.selling_price = rnd_selling_price
            product.save()
            test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'))
            self.assertEqual(product.selling_price, rnd_selling_price)
            self.assertEqual(product.discount_percent, rnd_discount)
            self.assertEqual(product.end_user_price, test_end_user_price)
            self.assertEqual(product.profit, test_end_user_price-product.cost_price)
        # case: all == 0
        product = Product.objects.create(name=get_random_string())
        self.assertEqual(product.end_user_price, 0)
        # case: all > 0
        rnd_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        rnd_discount = random.randint(1, 99)
        update_check_prices()
        # case: selling_price has changed
        rnd_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        update_check_prices()
        # case: discount_percent has changed
        rnd_discount = random.randint(1, 99)
        update_check_prices()
