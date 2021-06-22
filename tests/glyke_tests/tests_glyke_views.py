from os import name
from django.test import TestCase
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User

from glyke_back.models import *
from glyke_back.forms import *


class AddProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.basic_url = reverse('add_product')
        cls.test_user = User.objects.create(username='test_user', is_staff=False)
        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)

        cls.category_0_filters = Category.objects.create(name='category_0_filters')
        cls.category_1_filters = Category.objects.create(name='category_1_filters', filters='filter_1')
        cls.category_2_filters = Category.objects.create(name='category_2_filters', filters='filter_1, filter_2')

    def setUp(self):
        self.client.force_login(self.test_user_staff)

    def test_permissins(self):
        """If is_staff==False return 404"""
        response = self.client.get(self.basic_url) # case: staff
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.test_user) # case: logged-in user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)
        self.client.logout() # case: anonymous user
        response = self.client.get(self.basic_url)
        self.assertEqual(response.status_code, 404)

    def test_forms_instances(self):
        response = self.client.get(self.basic_url)
        self.assertIsInstance(response.context['category_form'], SelectCategoryProductForm)
        self.assertIsInstance(response.context['photos_form'], PhotosForm)
        self.assertIsInstance(response.context['product_form'], AddProductForm)
        self.assertNotIn('filter_form', response.context.keys())
        
    # TODO
    # def test_category_form(self):
    #     category = Category.objects.get(name='category_0_filters') # case: category w/o filters
    #     context_data = urlencode({'category': category.id})
    #     response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
    #     print(response.context['filter_form'].fields)
    #     category = Category.objects.get(name='category_2_filters') # case: category w/ 2 filters
    #     context_data = urlencode({'category': category.id})
    #     response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
    #     print(response.context['filter_form'].fields)


