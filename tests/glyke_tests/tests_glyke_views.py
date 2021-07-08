from django.core.validators import validate_comma_separated_integer_list
from django.db.models.expressions import Value
from django.test import TestCase
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import decimal
import random

from glyke_back.models import *
from glyke_back.forms import *
from .tests_glyke_models import get_random_temp_file


class AddProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.basic_url = reverse('add_product')
        cls.test_user = User.objects.create(username='test_user', is_staff=False)
        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)

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

    def test_permissions(self):
        """If is_staff==False return 404"""
        response = self.client.get(self.basic_url) # case: staff
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.test_user)    # case: logged-in user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()                       # case: anonymous user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, r'/oops/?error_suffix=photos+%28or+photos+form%29')
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
        rnd_cost_price = decimal.Decimal(random.randrange(1, 9999))/100
        rnd_selling_price = decimal.Decimal(random.randrange((rnd_cost_price*100), 9999))/100
        rnd_discount = random.randint(1, 80)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': f'product_rnd_profit',
                        'cost_price': rnd_cost_price,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)-rnd_cost_price).quantize(Decimal('0.01'))
        self.assertEqual(Product.objects.get(name='product_rnd_profit').profit, test_profit)

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
        rnd_selling_price = decimal.Decimal(random.randrange(100, 9999))/100
        rnd_discount = random.randint(1, 80)
        context_data = {'category': self.category_0_filters.id, # using category w/o filters here
                        'name': f'product_rnd_end_user_price',
                        'cost_price': 0,
                        'selling_price': rnd_selling_price,
                        'discount_percent': rnd_discount,
                        'tags': 'test_tag', 'stock': '1',}
        context_data_encoded = urlencode(context_data)
        self.client.post(self.basic_url, context_data_encoded, content_type="application/x-www-form-urlencoded")
        test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'))
        self.assertEqual(Product.objects.get(name='product_rnd_end_user_price').end_user_price, test_end_user_price)

class EditProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create(username='test_user', is_staff=False)
        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)

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

    def test_permissions(self):
        """If is_staff==False return 404"""
        response = self.client.get(self.basic_url) # case: staff
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.test_user)    # case: logged-in user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()                       # case: anonymous user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)

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
        for _ in range(1000):
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
            test_profit = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)-rnd_cost_price).quantize(Decimal('0.01'))
            self.assertEqual(self.product.profit, test_profit)

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
        test_end_user_price = Decimal(rnd_selling_price*Decimal(1-rnd_discount/100)).quantize(Decimal('0.01'))
        self.assertEqual(self.product.end_user_price, test_end_user_price)

class DeleteProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create(username='test_user', is_staff=False)
        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)

        cls.category_0_filters = Category.objects.create(name='category_0_filters')

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

    def test_permissions(self):
        """If is_staff==False return 404"""
        response = self.client.get(self.basic_url) # case: staff
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('products'))
        self.client.force_login(self.test_user)    # case: logged-in user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()                       # case: anonymous user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)

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
        self.assertTrue(str(response.url).startswith(reverse('smth_went_wrong')))

    def test_recover_active_product(self):
        """Checks redirect on trying to recover active product"""
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.all().first().is_active, True)
        response = self.client.get(self.basic_url + "?recover=y")
        self.assertTrue(str(response.url).startswith(reverse('smth_went_wrong')))


# TODO fix recalc profit test (line 327) (cause of end-user-price)










