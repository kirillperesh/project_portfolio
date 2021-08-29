from django.core.validators import validate_comma_separated_integer_list
from django.db.models.expressions import Value
from django.db.models.query_utils import Q
from django.http import response
from django.test import TestCase
from django.urls import reverse
from urllib.parse import urlencode, urlparse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import decimal
import random
from django.utils.crypto import get_random_string

from glyke_back.models import *
from glyke_back.forms import *
from .tests_glyke_models import get_random_temp_file

class TestPermissionsGETMixin:
    """
    Inheriting class has to inherit from django's TestCase
    self.basic_url has to be defined in inheriting class
    """
    @classmethod
    def setUpTestPermissionsUsers(cls, *, expected_permissions_status_codes):
        """Expects an expected GET request's status_code list as argument that maps [anonymous, regular, staff, superuser] users (is this exact order), e.g. [404, 304, 200, 200].
        expected_permissions_status_codes length must match the number of users + 1 (for anonymous).
        Sets up 3 test users (regular, staff, superuser)"""
        cls.test_user = User.objects.create(username='test_user', is_staff=False)
        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)
        # None is for anonymous user
        test_users_list = [None, cls.test_user, cls.test_user_staff, cls. test_user_superuser]
        # Checks if the number of expected status codes is correct
        if len(test_users_list) != len(expected_permissions_status_codes):
            raise AssertionError(f'Incorrect number of users or status codes ({cls.__name__})')
        # Maps users to their expected status codes (GET requests)
        cls.user_to_expected_status_dict = dict(zip(test_users_list, expected_permissions_status_codes))

    def test_permissions_GET(self):
        """Iterates through created users.
        Checks is response.status_code is correct for each user"""
        for user, expected_status_code in self.user_to_expected_status_dict.items():
            self.client.logout()
            if user is not None: # case: anonymous user
                self.client.force_login(user)
            response = self.client.get(self.basic_url)
            self.assertEqual(response.status_code, expected_status_code)

class AddProductViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[404,404,200,200]) # from TestPermissionsGETMixin
        cls.basic_url = reverse('add_product')
        cls.category_0_filters = Category.objects.create(name='category_0_filters')
        cls.category_1_filters = Category.objects.create(name='category_1_filters')
        cls.category_1_filters.filters.add('filter_1')
        cls.category_2_filters = Category.objects.create(name='category_2_filters')
        cls.category_2_filters.filters.add('filter_1', 'filter_2')

        cls.category_id_filters_dict = {cls.category_0_filters.id: list(cls.category_0_filters.filters.names()),  # case: category w/o filters
                                        cls.category_1_filters.id: list(cls.category_1_filters.filters.names()),  # case: category w/ 1 filter
                                        cls.category_2_filters.id: list(cls.category_2_filters.filters.names()),} # case: category w/ 2 filters
    def setUp(self):
        self.client.force_login(self.test_user_staff) # force_login before making requests because this is a staff-only view

    def test_forms_instances(self):
        """Checks if forms are rendered correctly on GET request"""
        response = self.client.get(self.basic_url)
        self.assertIsInstance(response.context['category_form'], SelectCategoryProductForm)
        self.assertIsInstance(response.context['photos_form'], PhotosForm)
        self.assertIsInstance(response.context['product_form'], AddProductForm)
        self.assertNotIn('filter_form', response.context.keys())

    def test_filter_form(self):
        """Checks if filter_form is created and rendered correctly based on category.id on POST request"""
        for category_id, filters_list in self.category_id_filters_dict.items():
            context_data = urlencode({'category': category_id})
            response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
            self.assertListEqual(list(response.context['filter_form'].fields.keys()), filters_list)

    def test_product_attributes_creation(self):
        """Checks if the product is created correctly with given attributes"""
        self.assertEqual(Product.objects.all().count(), 0)
        for category_id, filters_list in self.category_id_filters_dict.items():
            context_data = urlencode({'category': category_id,
                                      'filter_1': 'filter_1',
                                      'filter_2': 'filter_2',
                                      'name': f'product_{category_id}',
                                      'cost_price': '0','selling_price': '0', 'discount_percent': '0', 'tags': 'test_tag', 'stock': '1',})
            self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
            self.assertEqual(Product.objects.all().count(), category_id)
            product = Product.objects.get(name=f'product_{category_id}')
            self.assertEqual(list(product.attributes.keys()), filters_list)
            self.assertEqual(list(product.attributes.values()), filters_list)

    def test_product_gallery_creation(self):
        """Checks the error redirection on non-image upload file
        Checks if gallery of the product is created correctly"""
        self.assertEqual(Product.objects.all().count(), 0)
        test_file = SimpleUploadedFile("file.jpg", b"file_content")

        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': f'product_{self.category_0_filters.id}',
                        'cost_price': '0','selling_price': '0', 'discount_percent': '0', 'tags': 'test_tag', 'stock': '1',
                        'photos': [test_file,]}
        response = self.client.post(self.basic_url, context_data)
        expected_url = f"{reverse('smth_went_wrong')}?{'error_suffix=photos+%28or+photos+form%29'}"
        self.assertRedirects(response=response, expected_url=expected_url, target_status_code=200, status_code=302)
        self.assertEqual(Product.objects.all().count(), 1)
        product = Product.objects.get(name=f'product_{self.category_0_filters.id}')
        self.assertEqual(product.photos.title, f'product_{self.category_0_filters.id}_gallery')

    def test_profit_count(self):
        """Checks if the profit is (re)calculated on save()"""
        # case initial test (all 0)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': f'product_0_profit',
                        'cost_price': '0', 'selling_price': '0', 'discount_percent': '0',
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.assertEqual(Product.objects.get(name='product_0_profit').profit, 0)
        # case: random profit, w/ discount (other cases are tested in tests_glyke_models.py)
        rnd_name = get_random_string()
        rnd_cost_price = decimal.Decimal(random.randrange(1, 9999))/100
        rnd_selling_price = decimal.Decimal(random.randrange((rnd_cost_price*100), 9999))/100
        rnd_discount = random.randint(1, 80)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': rnd_name,
                        'cost_price': rnd_cost_price,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) - rnd_cost_price
        self.assertEqual(Product.objects.get(name=rnd_name).profit, test_profit)

    def test_end_user_price_count(self):
        """Checks if the end_user_price is (re)calculated on save()"""
        # case initial test (all 0)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': f'product_0_end_user_price',
                        'cost_price': '0', 'selling_price': '0', 'discount_percent': '0',
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.assertEqual(Product.objects.get(name='product_0_end_user_price').end_user_price, 0)
        # case: all > 0 (other cases are tested in tests_glyke_models.py)
        rnd_name = get_random_string()
        rnd_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        rnd_discount = random.randint(1, 80)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': rnd_name,
                        'cost_price': 0,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.assertEqual(Product.objects.get(name=rnd_name).end_user_price, test_end_user_price)

class EditProductViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[404,404,200,200]) # from TestPermissionsGETMixin
        cls.category_filters_1_2 = Category.objects.create(name='category_filters_1_2')
        cls.category_filters_1_2.filters.add('filter_1', 'filter_2')
        cls.category_filters_2_3 = Category.objects.create(name='category_filters_2_3')
        cls.category_filters_2_3.filters.add('filter_2', 'filter_3')

    def setUp(self):
        self.client.force_login(self.test_user_staff) # force_login before making requests because this is a staff-only view
        self.product = Product.objects.create(name='product',
                                              description='description text',
                                              category=self.category_filters_1_2,
                                              attributes={"filter_1": "1", "filter_2": "2"},
                                              stock=5,
                                              cost_price=10,
                                              selling_price=20,
                                              discount_percent=30,
                                              photos = photo_models.Gallery.objects.create(title='product_gallery')
                                             )
        self.product.tags.add('tag1, tag2')
        self.basic_url = reverse('edit_product', kwargs={'id': self.product.id})
        self.initial_products_count = Product.objects.all().count()
        self.basic_context_data = {'category': self.product.category.id,
                                   'filter_1': self.product.attributes['filter_1'],
                                   'filter_2': self.product.attributes['filter_2'],
                                   'name': self.product.name,
                                   'description': self.product.description,
                                   'cost_price': self.product.cost_price,
                                   'selling_price': self.product.selling_price,
                                   'discount_percent': self.product.discount_percent,
                                   'tags': ', '.join(list(self.product.tags.names())),
                                   'stock': self.product.stock,}

    def test_forms_instances(self):
        """Checks if forms are rendered correctly on GET request"""
        response = self.client.get(self.basic_url)
        self.assertIsInstance(response.context['category_form'], SelectCategoryProductForm)
        self.assertIsInstance(response.context['photos_form'], PhotosForm)
        self.assertIsInstance(response.context['product_form'], AddProductForm)
        self.assertIn('filter_form', response.context.keys())

    def test_initial_forms_data(self):
        """Checks if forms' initial data renders corrently"""
        response = self.client.get(self.basic_url)
        product_tags_str = ', '.join(list(self.product.tags.names()))
        self.assertEqual(response.context['category_form'].initial['category'], self.product.category)
        self.assertEqual(response.context['filter_form'].initial, self.product.attributes)
        self.assertEqual(response.context['photos_form'].initial, {})
        for field, initial in response.context['product_form'].initial.items():
            expected_initial = product_tags_str if field == 'tags' else getattr(self.product, field)
            self.assertEqual(initial, expected_initial)

    def test_category_switch(self):
        """Checks if the category and its filters switches properly on POST request"""
        initial_category = self.product.category
        switch_to_category = self.category_filters_2_3
        context_data = urlencode({'category': self.category_filters_2_3.id})
        # checking the initial data
        response = self.client.get(self.basic_url)
        self.assertEqual(response.context['category_form'].initial['category'], initial_category)
        self.assertEqual(list(response.context['filter_form'].fields.keys()), list(initial_category.filters.names()))
        self.assertEqual(response.context['filter_form'].initial, self.product.attributes)
        # checking data after category switching
        response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
        self.assertEqual(list(response.context['filter_form'].fields.keys()), list(switch_to_category.filters.names()))
        self.assertEqual(response.context['filter_form'].initial, self.product.attributes)

    def test_edit_product_except_category_and_name(self):
        """ Checks that the product is updated properly when anything except category and name is edited"""
        expected_data = {'filter_1': 'changed_filter_1',
                         'filter_2': 'changed_filter_2',
                         'description': 'changed_description',
                         'tags': 'changed_tag_1, changed_tag_2',
                         'stock': self.product.stock+1,
                         'cost_price': self.product.cost_price+1,
                         'selling_price': self.product.selling_price+1,
                         'discount_percent': self.product.discount_percent+1,
                         }
        # case: edit 1 by 1
        context_data = self.basic_context_data.copy()
        for field, expected_value in expected_data.items():
            context_data.update({field: expected_value})
            context_data_encoded = urlencode(context_data)
            self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
            self.product.refresh_from_db()
            self.assertEqual(Product.objects.all().count(), self.initial_products_count) # assert new products haven't been created
            if field.startswith('filter_'):
                actual_value = self.product.attributes[field]
            elif field == 'tags':
                actual_value = ', '.join(list(self.product.tags.names().order_by('name')))
            else:
                actual_value = getattr(self.product, field)
            self.assertEqual(actual_value, expected_value)
        # case: edit all at once
        actual_data = {}
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        self.assertEqual(Product.objects.all().count(), self.initial_products_count) # assert new products haven't been created
        for field in expected_data.keys():
            if field.startswith('filter_'):
                actual_data[field] = self.product.attributes[field]
            elif field == 'tags':
                actual_data[field] = ', '.join(list(self.product.tags.names().order_by('name')))
            else:
                actual_data[field] = getattr(self.product, field)
        self.assertEqual(actual_data, expected_data)

    def test_edit_product_category(self):
        """Checks if products category if changed properly"""
        actual_data = {}
        expected_data = {'filter_2': 'changed_filter_2',
                         'filter_3': 'changed_filter_3',
                         'category': self.category_filters_2_3.id,
                         }
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        self.assertEqual(Product.objects.all().count(), self.initial_products_count) # assert new products haven't been created
        for field in expected_data.keys():
            if field.startswith('filter_'):
                actual_data[field] = self.product.attributes[field]
            elif field.startswith('category'):
                actual_data[field] = getattr(self.product, field).id
            else: pass
        self.assertEqual(actual_data, expected_data)

    def test_edit_product_name(self):
        """Checks if product's name is changed (and back) properly (including gallery name) without changing its pk or creating new product"""
        initial_product_name, initial_product_id = self.product.name, self.product.id
        for new_name in ('changed_name_product', initial_product_name):
            context_data = self.basic_context_data.copy()
            context_data.update({'name': new_name,})
            context_data_encoded = urlencode(context_data)
            self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
            self.product.refresh_from_db()
            self.assertEqual(Product.objects.all().count(), self.initial_products_count) # assert new products haven't been created
            self.assertEqual(self.product.id, initial_product_id) # assert id hasn't changed
            self.assertEqual(self.product.name, new_name) # assert name has changed
            self.assertEqual(self.product.photos.title, new_name+"_gallery") # assert gallery name has changed

    def test_profit_recount(self):
        """Checks if the profit is (re)calculated on save()"""
        # case initial test (all 0)
        expected_data = {'cost_price': 0, 'selling_price': 0, 'discount_percent': 0,}
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        self.assertEqual(self.product.profit, 0)
        # case: random profit, w/ discount (other cases are tested in tests_glyke_models.py)
        rnd_cost_price = decimal.Decimal(random.randrange(1, 9999))/100
        rnd_selling_price = decimal.Decimal(random.randrange((rnd_cost_price*100), 9999))/100
        rnd_discount = random.randint(1, 80)
        expected_data = {'cost_price': rnd_cost_price,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,}
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) - rnd_cost_price
        self.assertEqual(self.product.profit, test_profit)
        self.assertEqual(self.product.profit, self.product.end_user_price-rnd_cost_price)

    def test_end_user_price_recount(self):
        """Checks if the profit is (re)calculated on save()"""
        # case initial test (all 0)
        expected_data = {'cost_price': 0, 'selling_price': 0, 'discount_percent': 0,}
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        self.assertEqual(self.product.end_user_price, 0)
        # case: all > 0 (other cases are tested in tests_glyke_models.py)
        rnd_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        rnd_discount = random.randint(1, 80)
        expected_data = {'cost_price': 0,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,}
        context_data = self.basic_context_data.copy()
        context_data.update(expected_data)
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        self.product.refresh_from_db()
        test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.assertEqual(self.product.end_user_price, test_end_user_price)

class DeleteProductViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[404,404,302,302]) # from TestPermissionsGETMixin
        cls.category_0_filters = Category.objects.create(name='category_0_filters')
        cls.expected_error_url = f"{reverse('smth_went_wrong')}?{'error_suffix=product+deletion+%28status+has+not+change%29'}"

    def setUp(self):
        self.client.force_login(self.test_user_staff) # force_login before making requests because this is a staff-only view
        self.product = Product.objects.create(name='product',
                                              description='description text',
                                              category=self.category_0_filters,
                                              stock=5,
                                              cost_price=10,
                                              selling_price=20,
                                              discount_percent=30,
                                              photos = photo_models.Gallery.objects.create(title='product_gallery')
                                             )
        self.product.tags.add('tag1, tag2')
        self.basic_url = reverse('delete_product', kwargs={'id': self.product.id})

    def test_delete_product(self):
        """Checks that the product is deactivated properly on delete url"""
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().first().is_active, True)
        self.client.get(self.basic_url)
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().first().is_active, False)

    def test_recover_product(self):
        """Checks that the product is recovered properly on delete url w/ recover query parameter"""
        self.assertEqual(Product.objects.all().count(), 1)
        Product.objects.all().update(is_active=False)
        self.assertEqual(Product.objects.all().first().is_active, False)
        self.client.get(self.basic_url + "?recover=y")
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().first().is_active, True)

    def test_delete_inactive_product(self):
        """Checks redirect on trying to delete inactive product"""
        self.assertEqual(Product.objects.all().count(), 1)
        Product.objects.all().update(is_active=False)
        self.assertEqual(Product.objects.all().first().is_active, False)
        response = self.client.get(self.basic_url)
        self.assertRedirects(response=response, expected_url=self.expected_error_url, target_status_code=200, status_code=302)

    def test_recover_active_product(self):
        """Checks redirect on trying to recover active product"""
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().first().is_active, True)
        response = self.client.get(self.basic_url + "?recover=y")
        self.assertRedirects(response=response, expected_url=self.expected_error_url, target_status_code=200, status_code=302)

class ProductsStaffViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[404,404,200,200]) # from TestPermissionsGETMixin

    def setUp(self):
        self.client.force_login(self.test_user_staff) # force_login before making requests because this is a staff-only view
        self.basic_url = reverse('products_staff')

    def test_initial_products_queryset(self):
        """Checks if the view receives all the products instances"""
        products_count = random.randint(25, 50)
        for i in range(products_count):
            Product.objects.create(name=f'{i}_{get_random_string()}')
        response = self.client.get(self.basic_url)
        view_products_queryset = response.context['products'].order_by('id')
        self.assertEqual(view_products_queryset.all().count(), products_count)
        self.assertQuerysetEqual(view_products_queryset, Product.objects.all())

class AddToCartViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[302,405,405,405]) # from TestPermissionsGETMixin

    def setUp(self):
        self.client.force_login(self.test_user) # force_login before making requests because this is a logged-in-only view
        self.product = Product.objects.create(name=get_random_string(length=10))
        self.basic_url = reverse('add_to_cart')

    def test_current_order_creation_on_user_log_in(self):
        """Checks if a current order is created on user login, if there is none"""
        # test_user is already logged in, so there has to be 1 'current_order'
        self.assertEqual(Order.objects.all().count(), 1)
        self.assertEqual(self.test_user.orders.filter(status='CUR').count(), 1)
        self.client.logout()
        self.assertEqual(Order.objects.all().count(), 1)
        self.assertEqual(self.test_user.orders.filter(status='CUR').count(), 1)
        self.client.force_login(self.test_user_staff) # its test_user_staff's first log-in so a 'current_order' has to be created for this user
        self.assertEqual(Order.objects.all().count(), 2)
        self.assertEqual(self.test_user_staff.orders.filter(status='CUR').count(), 1)
        self.client.logout()
        self.assertEqual(Order.objects.all().count(), 2)
        self.assertEqual(self.test_user_staff.orders.filter(status='CUR').count(), 1)
        self.client.force_login(self.test_user_staff)
        self.assertEqual(Order.objects.all().count(), 2)
        self.assertEqual(self.test_user_staff.orders.filter(status='CUR').count(), 1)

    def test_order_line_creation(self):
        """Checks if a product is being added to the cart properly"""
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Order.objects.all().count(), 1)
        self.assertEqual(self.test_user.orders.filter(status='CUR').count(), 1)
        self.assertEqual(self.test_user.orders.filter(status='CUR').first().order_lines.count(), 0)
        context_data = urlencode({'product_id': self.product.id})
        for i in range(3): # also checks if the addToCart url increments existing order_line's quantity
            self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
            self.assertEqual(Product.objects.all().count(), 1)
            self.assertEqual(Order.objects.all().count(), 1)
            self.assertEqual(self.test_user.orders.filter(status='CUR').count(), 1)
            self.assertEqual(self.test_user.orders.filter(status='CUR').first().order_lines.count(), 1)
            self.assertEqual(self.test_user.orders.filter(status='CUR').first().order_lines.first().quantity, i+1)
            self.assertEqual(self.test_user.orders.filter(status='CUR').first().order_lines.first().product, self.product)

    def test_add_to_cart_redirection(self):
        """Checks if the view redirects properly"""
        context_data = urlencode({'product_id': self.product.id})
        response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/') # default redirection url
        next_parameter = reverse('products')
        context_data = urlencode({'product_id': self.product.id,
                                  'next': next_parameter})
        response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_parameter)

    def test_no_current_order_response(self):
        """Check if the view redirect correctly if there is no current order"""
        Order.objects.all().delete()
        context_data = urlencode({'product_id': self.product.id})
        response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
        expected_url = f"{reverse('smth_went_wrong')}?{'error_suffix=order+%28probably+there+is+none%29'}"
        self.assertRedirects(response=response, expected_url=expected_url, target_status_code=200, status_code=302)

class CartViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[302,200,200,200]) # from TestPermissionsGETMixin

    def setUp(self):
        self.client.force_login(self.test_user) # force_login before making requests because this is a logged-in-only view
        self.product = Product.objects.create(name=get_random_string(length=10))
        self.basic_url = reverse('cart')

    def test_no_current_order_response(self):
        """Check if the view redirect correctly if there is no current order"""
        Order.objects.all().delete()
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(r'/oops/?error_suffix='))

class ClearCartViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[302,302,302,302]) # from TestPermissionsGETMixin
        cls.test_user_2 = User.objects.create(username='test_user_2', is_staff=False)
        cls.number_of_order_lines = 3

    def setUp(self):
        self.client.force_login(self.test_user) # force_login before making requests because this is a logged-in-only view
        self.order = Order.objects.create(customer=self.test_user)
        # self.product = Product.objects.create(name=get_random_string(length=10))
        self.basic_url = reverse('clear_cart', kwargs={'id': self.order.id})

    def test_clear_cart_permissions(self):
        """Checks if clear_cart_view permissions work properly.
        A cart can be cleared only by its owner or a staff user"""
        Order.objects.all().delete()
        self.order_user_1 = Order.objects.create(customer=self.test_user, status='CUR')
        self.basic_url_user_1 = reverse('clear_cart', kwargs={'id': self.order_user_1.id})
        self.order_user_2 = Order.objects.create(customer=self.test_user_2, status='CUR')
        self.basic_url_user_2 = reverse('clear_cart', kwargs={'id': self.order_user_2.id})
        self.order_staff = Order.objects.create(customer=self.test_user_staff, status='CUR')
        self.basic_url_staff = reverse('clear_cart', kwargs={'id': self.order_staff.id})

        for user in (self.test_user, self.test_user_2, self.test_user_staff):
            # setting up for every user
            OrderLine.objects.all().delete()
            self.client.logout()
            self.client.force_login(user)
            for _ in range(self.number_of_order_lines):
                rnd_product = Product.objects.create(name=get_random_string(length=10))
                OrderLine.objects.create(parent_order=self.order_user_1, product = rnd_product)
                OrderLine.objects.create(parent_order=self.order_user_2, product = rnd_product)
                OrderLine.objects.create(parent_order=self.order_staff, product = rnd_product)
            # case: regular user's order
            # only the owner (user) and the staff should be able to clear it
            self.assertEqual(Order.objects.filter(customer=self.test_user, status='CUR').count(), 1)
            self.assertEqual(self.order_user_1.order_lines.count(), self.number_of_order_lines)
            response = self.client.get(self.basic_url_user_1)
            self.assertEqual(Order.objects.filter(customer=self.test_user, status='CUR').count(), 1)
            if user == self.test_user_2:
                self.assertEqual(self.order_user_1.order_lines.count(), self.number_of_order_lines)
                self.assertEqual(response.status_code, 404)
            else:
                self.assertFalse(self.order_user_1.order_lines.exists())
                self.assertRedirects(response=response, expected_url=reverse('products'), target_status_code=200, status_code=302)
            # case: regular user_2's order
            # only the owner (user_2) and the staff should be able to clear it
            self.assertEqual(Order.objects.filter(customer=self.test_user_2, status='CUR').count(), 1)
            self.assertEqual(self.order_user_2.order_lines.count(), self.number_of_order_lines)
            response = self.client.get(self.basic_url_user_2)
            self.assertEqual(Order.objects.filter(customer=self.test_user_2, status='CUR').count(), 1)
            if user == self.test_user:
                self.assertEqual(self.order_user_2.order_lines.count(), self.number_of_order_lines)
                self.assertEqual(response.status_code, 404)
            else:
                self.assertFalse(self.order_user_2.order_lines.exists())
                self.assertRedirects(response=response, expected_url=reverse('products'), target_status_code=200, status_code=302)
            # case: staff user's order
            # only the staff should be able to clear this order
            self.assertEqual(Order.objects.filter(customer=self.test_user_staff, status='CUR').count(), 1)
            self.assertEqual(self.order_staff.order_lines.count(), self.number_of_order_lines)
            response = self.client.get(self.basic_url_staff)
            self.assertEqual(Order.objects.filter(customer=self.test_user_staff, status='CUR').count(), 1)
            if user == self.test_user_staff:
                self.assertFalse(self.order_staff.order_lines.exists())
                self.assertRedirects(response=response, expected_url=reverse('products'), target_status_code=200, status_code=302)
            else:
                self.assertEqual(self.order_staff.order_lines.count(), self.number_of_order_lines)
                self.assertEqual(response.status_code, 404)

    def test_clear_cart_failure_handling(self):
        """Checks if the view redirect correctly to 'smth_went_wrong' if order_lines' deletion failed"""
        from django.dispatch.dispatcher import receiver
        from django.db.models.signals import post_delete
        @receiver(post_delete,
                  sender=OrderLine,
                  dispatch_uid='save_order_line_test_1')
        def order_line_post_delete_erroneous_handler(sender, instance, **kwargs):
            """A signal handler that add an order_line to the Order that had to be cleared for testing purposes"""
            if instance.parent_order.order_lines.count() == 0:
                rnd_product = Product.objects.create(name=get_random_string(length=10))
                OrderLine.objects.create(parent_order=self.order, product = rnd_product)
            instance.parent_order.save() # this is a part of the original non-erroneous handler

        rnd_product = Product.objects.create(name=get_random_string(length=10))
        OrderLine.objects.create(parent_order=self.order, product = rnd_product)
        response = self.client.get(self.basic_url)
        self.assertTrue(self.order.order_lines.exists())
        expected_url = f"{reverse('smth_went_wrong')}?{'error_suffix=cart+%28tried+to+clear+it%2C+but+it+did+not+become+empty%29'}"
        self.assertRedirects(response=response, expected_url=expected_url, target_status_code=200, status_code=302)

class CartViewTest(TestPermissionsGETMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.setUpTestPermissionsUsers(expected_permissions_status_codes=[302,200,200,200]) # from TestPermissionsGETMixin

    def setUp(self):
        self.client.force_login(self.test_user) # force_login before making requests because this is a staff-only view
        self.basic_url = reverse('cart')

    def create_rnd_order_line(self, parent_order, stock=random.randint(1,9)):
        """Return a random (rnd_order_line, rnd_product) tuple"""
        rnd_product = Product.objects.create(name=get_random_string(),
                                             stock=stock,
                                             selling_price = decimal.Decimal(random.randrange(100, 9999))/100,
                                             discount_percent = random.choice((0, 10, 20)),
                                             )
        rnd_order_line = OrderLine.objects.create(parent_order=parent_order,
                                                  product = rnd_product,
                                                  quantity = random.randint(1, stock)
                                                  )
        return (rnd_order_line, rnd_product)

    def test_current_order_orderlines(self):
        """Checks if the view receives all the order_line instances needed"""
        current_order = self.test_user.orders.filter(status='CUR').order_by('-created').first()
        # tests different order_lines number cases: (0, 1, 2, 5, 20)
        for order_lines_count in (0, 1, 2, 5, 20):
            OrderLine.objects.all().delete()
            for _ in range(order_lines_count):
                self.create_rnd_order_line(parent_order = current_order)
            response = self.client.get(self.basic_url)
            view_current_order = response.context['order']
            view_order_lines_queryset = response.context['order_lines']
            self.assertEqual(view_current_order, current_order)
            self.assertQuerysetEqual(view_order_lines_queryset, current_order.order_lines.all())

    def test_current_order_instance(self):
        """Checks if the view receives the right instance of the Order model"""
        Order.objects.create(status='CUR', customer=self.test_user) # right status, right user
        Order.objects.create(status='CAN', customer=self.test_user) # wrong status, right user
        Order.objects.create(status='CAN', customer=self.test_user_staff) # wrong status, wrong user
        self.assertEqual(Order.objects.filter(status='CUR').count(), 2)
        self.assertEqual(Order.objects.all().count(), 4)
        current_order = self.test_user.orders.filter(status='CUR').order_by('-created').first()
        for _ in range(3): self.create_rnd_order_line(parent_order=current_order)
        response = self.client.get(self.basic_url)
        view_current_order = response.context['order']
        view_order_lines_queryset = response.context['order_lines']
        self.assertEqual(view_current_order, current_order)
        self.assertQuerysetEqual(view_order_lines_queryset, current_order.order_lines.all())

    def test_remove_order_line(self):
        """Checks if removing order_lines works as expected. Also tests if the view avoids duplicating lines properly"""
        current_order = self.test_user.orders.filter(status='CUR').order_by('-created').first()
        context_data = dict()
        products_id_list = list()
        initial_lines_count = 6 # it's 6 so that different numbers of lines to delete can be tested
        for line_num in range(initial_lines_count):
            rnd_order_line, rnd_product = self.create_rnd_order_line(parent_order=current_order)
            products_id_list.append(str(rnd_product.id))
            # sometimes add an additiontal copy of a parameter to test duplicating avoidance
            if line_num % 2 == 0: products_id_list.append(str(rnd_product.id))
            context_data[f'quantity_{rnd_order_line.line_number}'] = rnd_order_line.quantity
        context_data['products_id'] = products_id_list

        self.assertEqual(current_order.order_lines.count(), initial_lines_count)
        response = self.client.post(self.basic_url, context_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_order.order_lines.count(), initial_lines_count)

        products_id_list = list(set(products_id_list)) # set() is not working with random.choice() below
        expected_lines_count = initial_lines_count
        # check diffent numbers of lines deleted at a time (1, 2, the rest)
        for lines_to_delete_count in (1, 2, initial_lines_count-3):
            context_data = dict()
            for _ in range(lines_to_delete_count):
                rnd_line_to_delete_product_id = random.choice(products_id_list)
                products_id_list.remove(rnd_line_to_delete_product_id) # remove this rnd id from POST parameters
    # TODO comment
            for product_left_id in products_id_list:
                order_line_left = current_order.order_lines.filter(product__id=product_left_id).first()
                context_data[f'quantity_{order_line_left.line_number}'] = order_line_left.quantity
# TODO comment

            context_data['products_id'] = products_id_list
            self.assertEqual(current_order.order_lines.count(), expected_lines_count)
            expected_lines_count -= lines_to_delete_count
            response = self.client.post(self.basic_url, context_data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(current_order.order_lines.count(), expected_lines_count)

    def test_order_lines_quantity_update(self):
        """Checks if each order_line's quantity can be updated properly"""
        current_order = self.test_user.orders.filter(status='CUR').order_by('-created').first()
        context_data = dict()
        products_id_list = list()
        initial_lines_count = 4 # it's 4 so that different numbers of lines to update can be tested (1, 2, the rest)
        for _ in range(initial_lines_count):
            rnd_order_line, rnd_product = self.create_rnd_order_line(parent_order=current_order)
            products_id_list.append(str(rnd_product.id))
            context_data[f'quantity_{rnd_order_line.line_number}'] = rnd_order_line.quantity
        context_data['products_id'] = products_id_list
        # initial check
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['order_lines'])
        for order_line in response.context['order_lines'].all().order_by('line_number'):
            self.assertEqual(order_line.quantity, context_data[f'quantity_{order_line.line_number}'])
        # check diffent numbers of lines update at a time (0, 1, 2, the rest)
        for changed_lines_count in (0, 1, 2, initial_lines_count):
            changed_lines_numbers = list()
            for _ in range(changed_lines_count):
                while True: # making sure the same line won't get updated more than once
                    rnd_order_line_number = random.randint(1, initial_lines_count)
                    if rnd_order_line_number not in changed_lines_numbers:
                        changed_lines_numbers.append(rnd_order_line_number)
                        break
                while True: # making sure the new_quantity is different from the old one
                    new_quantity = random.randint(1, 9)
                    if new_quantity != context_data[f'quantity_{rnd_order_line_number}']:
                        context_data[f'quantity_{rnd_order_line_number}'] = new_quantity
                        break
            # check eache set of updated lines
            response = self.client.post(self.basic_url, context_data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['order_lines'])
            for order_line in response.context['order_lines'].all().order_by('line_number'):
                self.assertEqual(order_line.quantity, context_data[f'quantity_{order_line.line_number}'])

    def test_post_parameters(self):
        """
        TODO"""

        current_order = self.test_user.orders.filter(status='CUR').order_by('-created').first()
        context_data = dict()
        products_id_list = list()
        initial_lines_count = 3 # it's 6 so that different numbers of lines to delete can be tested
        for line_num in range(initial_lines_count):
            rnd_order_line, rnd_product = self.create_rnd_order_line(parent_order=current_order)
            products_id_list.append(str(rnd_product.id))
            # sometimes add an additiontal copy of a parameter to test duplicating avoidance
            if line_num % 2 == 0: products_id_list.append(str(rnd_product.id))
            context_data[f'quantity_{rnd_order_line.line_number}'] = rnd_order_line.quantity
        # context_data['products_id'] = products_id_list

        self.assertEqual(current_order.order_lines.count(), initial_lines_count)
        response = self.client.post(self.basic_url, context_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_order.order_lines.count(), initial_lines_count)

# # TODO add checks that quantity and id paarmeters have to be passed at POST