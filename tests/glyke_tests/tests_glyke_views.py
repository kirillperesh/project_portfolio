from django.test import TestCase
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

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
        cls.category_1_filters = Category.objects.create(name='category_1_filters')
        cls.category_1_filters.filters.add('filter_1')
        cls.category_2_filters = Category.objects.create(name='category_2_filters')
        cls.category_2_filters.filters.add('filter_1', 'filter_2')

        cls.category_id_filters_dict = {cls.category_0_filters.id: list(cls.category_0_filters.filters.names()),  # case: category w/o filters
                                        cls.category_1_filters.id: list(cls.category_1_filters.filters.names()),  # case: category w/ 1 filter
                                        cls.category_2_filters.id: list(cls.category_2_filters.filters.names()),} # case: category w/ 2 filters

    def setUp(self):
        self.client.force_login(self.test_user_staff) # force_login before making requests because this is a staff-only view

    def test_permissins(self):
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
            response = self.client.post(self.basic_url, context_data, content_type="application/x-www-form-urlencoded")
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









