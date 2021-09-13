from logging import raiseExceptions
from os import name
from types import prepare_class
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

        cls.order = Order.objects.create(number=1, customer=None)
        cls.order_line = OrderLine.objects.create(parent_order=cls.order, product=cls.product_child)

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

    def test_category_child_level(self):
        """Aseert categories' child_level update as expected on CRUD"""
        test_cat = Category.objects.create(name='Parent cat 2')
        test_cat_2 = Category.objects.create(name='Sub-parent cat 2', parent = self.parent_cat)
        self.assertEqual(self.parent_cat.child_level, 0)
        self.assertEqual(test_cat.child_level, 0)
        self.assertEqual(self.sub_parent_cat.child_level, 1)
        self.assertEqual(test_cat_2.child_level, 1)
        self.assertEqual(self.child_cat.child_level, 2)
        test_cat.parent = self.child_cat
        test_cat.save()
        test_cat_2.parent = None
        test_cat_2.save()
        self.assertEqual(self.parent_cat.child_level, 0)
        self.assertEqual(test_cat.child_level, 3)
        self.assertEqual(self.sub_parent_cat.child_level, 1)
        self.assertEqual(test_cat_2.child_level, 0)
        self.assertEqual(self.child_cat.child_level, 2)
        self.parent_cat.delete()
        self.sub_parent_cat.refresh_from_db()
        self.child_cat.refresh_from_db()
        test_cat.refresh_from_db()
        self.assertEqual(self.sub_parent_cat.child_level, 0)
        self.assertEqual(self.child_cat.child_level, 1)
        self.assertEqual(test_cat.child_level, 2)
        self.assertEqual(test_cat_2.child_level, 0)

    def test_category_ordering_indices_update(self):
        """Assert categories' ordering_indices update properly"""
        Category.objects.all().delete()
        Product.objects.all().delete()
        category_a = Category.objects.create(name='a')
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        Category.objects.create(name='b')
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 2)
        Category.objects.create(name='c')
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 3)
        category_a_a = Category.objects.create(name='aa', parent=category_a)
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='aa').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 3)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 4)
        Category.objects.create(name='aaa', parent=category_a_a)
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='aa').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='aaa').ordering_index, 3)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 4)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 5)
        Category.objects.create(name='ba')
        self.assertEqual(Category.objects.get(name='a').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='aa').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='aaa').ordering_index, 3)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 4)
        self.assertEqual(Category.objects.get(name='ba').ordering_index, 5)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 6)
        Category.objects.get(name='a').delete()
        self.assertEqual(Category.objects.get(name='aa').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='aaa').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 3)
        self.assertEqual(Category.objects.get(name='ba').ordering_index, 4)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 5)
        Category.objects.get(name='aaa').delete()
        self.assertEqual(Category.objects.get(name='aa').ordering_index, 1)
        self.assertEqual(Category.objects.get(name='b').ordering_index, 2)
        self.assertEqual(Category.objects.get(name='ba').ordering_index, 3)
        self.assertEqual(Category.objects.get(name='c').ordering_index, 4)


    # TODO add category tests here

    def test_get_deleted_instance_on_delete(self):
        """Assert a deleted instance is created on_delete"""
        self.product_child.delete()
        self.order_line.refresh_from_db()
        deleted_product_auto = Product.objects.get(name='_deleted_')
        self.assertEqual(self.order_line.product, deleted_product_auto)

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
        order_no_user = Order.objects.create(number=rnd_str, customer=None)
        self.assertIn('no_name', str(order_no_user))
        order = Order.objects.create(number=rnd_str, customer=self.user_not_staff)
        self.assertIn(self.user_not_staff.username, str(order))
        orderline_no_user = OrderLine.objects.create(parent_order=order_no_user, product=product)
        self.assertIn('no_name | Line: 1', str(orderline_no_user))
        orderline = OrderLine.objects.create(parent_order=order, product=product)
        self.assertIn(f'{self.user_not_staff.username} | Line: 1', str(orderline))

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

    def test_photos_rename_on_product_rename(self):
        """Checks if product's gallery & photos are renamed properly when the product is renamed"""
        rnd_product_name = get_random_string(length=20)
        gallery = create_gallery(title=rnd_product_name)
        # create 4 random photos and add them to product's gallery
        for _ in range(4):
            rnd_photo_name = f'{get_random_string()}_{rnd_product_name}' # this part is usually done in the view
            img_file = SimpleUploadedFile(rnd_photo_name, b"these are the file contents")
            photo = photo_models.Photo.objects.create(image=img_file, title=rnd_photo_name, slug=slugify(rnd_photo_name))
            gallery.photos.add(photo)
        product = Product.objects.create(name=rnd_product_name, photos=gallery)
        self.assertTrue(product.photos.photos.all().exists())
        self.assertQuerysetEqual(product.photos.photos.all().order_by('id'), photo_models.Photo.objects.all().order_by('id'))
        self.assertEqual(gallery.slug, slugify(product.name + "_gallery"))
        for photo in product.photos.photos.all():
            self.assertTrue(photo.title.endswith(f'_{rnd_product_name}'))
            self.assertTrue(photo.slug.endswith(f'_{slugify(rnd_product_name)}'))
        # rename the product, all of its photos and gallery has to be renamed on save() as well
        rnd_product_name = get_random_string(length=20)
        product.name = rnd_product_name
        product.save()
        self.assertQuerysetEqual(product.photos.photos.all().order_by('id'), photo_models.Photo.objects.all().order_by('id'))
        self.assertEqual(gallery.slug, slugify(product.name + "_gallery"))
        for photo in product.photos.photos.all():
            self.assertTrue(photo.title.endswith(f'_{rnd_product_name}'))
            self.assertTrue(photo.slug.endswith(f'_{slugify(rnd_product_name)}'))

    def test_product_save_profit_update(self):
        """Assert product save method updates profit attr"""
        def update_check_prices():
            product.cost_price = rnd_cost_price
            product.discount_percent = rnd_discount
            product.selling_price = rnd_selling_price
            product.save()
            test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) - rnd_cost_price
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
            test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
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

    def test_orderline_autoinc(self):
        """Assert line auto-numering in checks work properly"""
        order_no_user = Order.objects.create()
        for _ in range(5): # i'm guessing 5 lines is more than enough
            product = Product.objects.create(name=get_random_string(length=12))
            order_line = OrderLine.objects.create(parent_order=order_no_user, product=product)
            self.assertEqual(order_line.line_number, order_no_user.order_lines.count())
        # deletes all lines one by one, except for the last one
        # the line_number of each following line has to be decremented by 1 (keeping the initial line order)
        for _ in range(order_no_user.order_lines.count()-1):
            order_no_user.order_lines.first().delete()
            expected_line_number = 1
            for order_line in order_no_user.order_lines.all():
                self.assertEqual(order_line.line_number, expected_line_number)
                expected_line_number += 1

    def test_orderline_duplicating_avoiding(self):
        """Checks if an existing order_line instance's quantity is incremented properly, if a new order_line instance of the same product is tried to be created. Also check if a duplicating instance of order_line is not created."""
        quantity_1 = random.randint(1, 100)
        quantity_2 = random.randint(1, 100)
        OrderLine.objects.all().delete()
        order = Order.objects.create()
        self.assertEqual(OrderLine.objects.all().count(), 0)
        self.assertEqual(order.order_lines.count(), 0)
        # creating 1 line of product A: 1 created
        OrderLine.objects.create(parent_order=order, product=self.product_child, quantity=quantity_1)
        self.assertEqual(OrderLine.objects.all().count(), 1)
        self.assertEqual(order.order_lines.count(), 1)
        self.assertEqual(order.order_lines.first().quantity, quantity_1)
        # creating 2 line of product A: 0 created, line 1 updated
        OrderLine.objects.create(parent_order=order, product=self.product_child, quantity=quantity_2)
        self.assertEqual(OrderLine.objects.all().count(), 1)
        self.assertEqual(order.order_lines.count(), 1)
        self.assertEqual(order.order_lines.first().quantity, quantity_1+quantity_2)

    def test_order_calculating(self):
        """Checks if Order's total prices are calculated properly"""
        expected_order_cost_price = 0
        expected_order_selling_price = 0
        expected_order_end_user_price = 0
        order = Order.objects.create()
        for i in range(3):
            self.assertEqual(order.cost_price, expected_order_cost_price)
            self.assertEqual(order.selling_price, expected_order_selling_price)
            self.assertEqual(order.end_user_price, expected_order_end_user_price)
            # add 3 order_lines
            # has to be different product each time, because same product lines get summed up
            product = Product.objects.create(name=get_random_string(),
                                             cost_price = decimal.Decimal(random.randrange(100, 9999))/100,
                                             selling_price = decimal.Decimal(random.randrange((self.product_child.cost_price*100), 9999))/100,
                                             discount_percent = random.randint(0, 4) * 10,
                                             )
            rnd_quantity = random.randint(1, 4)
            OrderLine.objects.create(parent_order=order,
                                     product=self.product_child,
                                     quantity=rnd_quantity)
            # update expected values
            expected_order_cost_price += self.product_child.cost_price * rnd_quantity
            expected_order_selling_price += self.product_child.selling_price * rnd_quantity
            expected_order_end_user_price += self.product_child.end_user_price * rnd_quantity

    def test_order_update_on_orderline_save(self):
        """Checks if Order's save() method is called on any of its orderlines' save() and if its prices are recalculated properly"""
        initial_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        multiplier = random.randint(1, 5)
        order = Order.objects.create()
        self.product_child.selling_price = initial_selling_price
        self.product_child.save()
        order_line= OrderLine.objects.create(parent_order=order, product=self.product_child)
        self.assertEqual(order.selling_price, initial_selling_price)
        # case: quantity update
        order_line.quantity = multiplier
        order_line.save()
        self.assertEqual(order.selling_price, initial_selling_price*multiplier)
        # case: price update
        self.product_child.selling_price = initial_selling_price*multiplier
        order_line.quantity = 1
        order_line.save()
        self.assertEqual(order.selling_price, initial_selling_price*multiplier)

    def test_order_update_on_orderline_delete(self):
        """Checks if Order's save() method is called on any of its orderlines' delete() and if its prices are recalculated properly"""
        initial_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        order = Order.objects.create()
        self.product_child.selling_price = initial_selling_price
        self.product_child.save()
        order_line = OrderLine.objects.create(parent_order=order, product=self.product_child)
        self.assertEqual(order.selling_price, initial_selling_price)
        # case: no orderlines
        order_line.delete()
        self.assertEqual(order.selling_price, 0)

    def test_order_items_total_update(self):
        """Checks if Order's items_total is calculated properly"""
        expected_items_total = 0
        OrderLine.objects.all().delete()
        order = Order.objects.create()
        self.assertEqual(order.items_total, expected_items_total)
        for i in range(5):
            expected_order_lines_count = i + 1
            rnd_product = Product.objects.create(name=get_random_string(), category = self.child_cat)
            rnd_quantity = random.randint(1, 100)
            expected_items_total += rnd_quantity
            # creating a line of a random product: 1 created, order's total updated
            order_line = OrderLine.objects.create(parent_order=order, product=rnd_product, quantity=rnd_quantity)
            self.assertEqual(OrderLine.objects.all().count(), expected_order_lines_count)
            self.assertEqual(order.order_lines.count(), expected_order_lines_count)
            self.assertEqual(order.items_total, expected_items_total)
            # updating previous line's quantity: 0 created, order's total updated
            new_rnd_quantity = random.randint(1, 100)
            expected_items_total += new_rnd_quantity - rnd_quantity
            order_line.quantity = new_rnd_quantity
            order_line.save()
            self.assertEqual(OrderLine.objects.all().count(), expected_order_lines_count)
            self.assertEqual(order.order_lines.count(), expected_order_lines_count)
            self.assertEqual(order.items_total, expected_items_total)

    def test_order_get_latest_methods(self):
        """Checks if OrderFiltersManager.get_latest_.. methods work properly"""
        # check only 'CUR' method for now
        order_current_oldest = Order.objects.create(status='CUR')
        order_current_latest = Order.objects.create(status='CUR')
        order_canceled_latest = Order.objects.create(status='CAN')
        self.assertNotEqual(Order.objects.get_latest_current(), order_current_oldest)
        self.assertEqual(Order.objects.get_latest_current(), order_current_latest)


