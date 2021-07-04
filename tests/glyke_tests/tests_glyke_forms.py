from django.test import TestCase

from glyke_back.models import *
from glyke_back.forms import *


class AddProductFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.correct_field_list = ['cost_price', 'selling_price', 'discount_percent', 'name', 'description', 'created_by', 'tags', 'stock', 'main_photo']
        cls.decimal_test_fields = ['cost_price', 'selling_price']
        cls.positive_test_fields = cls.decimal_test_fields + ['discount_percent','stock']
        cls.required_field_list = cls.positive_test_fields + ['name', 'tags']
        cls.product = Product.objects.create(name='not_unique_name')

    def setUp(self):
        self.base_form_data = {'name': 'unique_name', 'tags': 'tag1 tag2', 'stock': 0, 'cost_price': 0, 'selling_price': 0, 'discount_percent': 0,}

    def test_fields_list(self):
        """Checks if the form returns correct fields"""
        test_form = AddProductForm()
        self.assertListEqual(list(test_form.fields.keys()), self.correct_field_list)

    def test_required_fields(self):
        """Checks required fields"""
        valid_form = AddProductForm(data={})
        self.assertEqual(len(valid_form.errors), len(self.required_field_list))
        for field_name in valid_form.errors:
            self.assertIn(field_name, self.required_field_list)
            self.assertEqual(valid_form.errors[field_name], ['This field is required.'])

    def test_unique_name(self):
        """Check that the name of a product has to be unique"""
        self.base_form_data['name'] = Product.objects.get(name='not_unique_name').name
        invalid_form = AddProductForm(data=self.base_form_data)
        self.assertEqual(invalid_form.errors['name'], ['Product with this Name already exists.'])

    def test_negative_number(self):
        """Check that stock, prices and discount cannot be negative"""
        for field in self.positive_test_fields:
            self.base_form_data[field] = -1
            invalid_form = AddProductForm(data=self.base_form_data)
            self.assertEqual(invalid_form.errors[field], ['Ensure this value is greater than or equal to 0.'])

    def test_decimal_fields(self):
        """Check that decimal fields work properly (2 decimal, 6 total)"""
        decimal_cases = [1234567, 12345.1, 123.123]
        for field in self.decimal_test_fields:
            for case in decimal_cases:
                self.base_form_data[field] = case
                invalid_form = AddProductForm(data=self.base_form_data)
                self.assertIn('Ensure that there are no more than', invalid_form.errors[field][0])


class SelectCategoryProductFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category_1 = Category.objects.create(name='category_1')                                  # case: no children, no parents
        cls.category_2 = Category.objects.create(name='category_2')                                  # case: 2 children, no parents
        cls.category_2_1 = Category.objects.create(name='category_2_1', parent=cls.category_2)       # case: no children, 1 parent
        cls.category_2_2 = Category.objects.create(name='category_2_2', parent=cls.category_2)       # case: 3 children, 1 parent
        cls.category_2_2_1 = Category.objects.create(name='category_2_2_1', parent=cls.category_2_2) # case: no children, 2 parent
        cls.category_2_2_2 = Category.objects.create(name='category_2_2_2', parent=cls.category_2_2) # case: no children, 2 parent
    def setUp(self):
        self.test_form = SelectCategoryProductForm()

    def test_fields_list(self):
        """Checks if the form returns correct fields"""
        self.assertListEqual(list(self.test_form.fields.keys()), ['category',])

    def test_choices_count(self):
        """Checks if the form returns correct number of choices"""
        form_queryset = self.test_form.fields['category'].choices.queryset.order_by('id')
        active_categories = Category.objects.filter(is_active=True).order_by('id')
        self.assertQuerysetEqual(form_queryset, active_categories)

    def test_active_choices_count(self):
        """Iterates over all categories deactivating them and checks if the form return correct number of choices"""
        for category in Category.objects.all().order_by('-id'):
            category.is_active = False
            category.save()
            form_queryset = self.test_form.fields['category'].choices.queryset.order_by('id')
            active_categories = Category.objects.filter(is_active=True).order_by('id')
            self.assertQuerysetEqual(form_queryset, active_categories)

    def test_is_valid(self):
        # case: valid
        valid_form = SelectCategoryProductForm(data={'category': self.category_1})
        self.assertTrue(valid_form.is_valid())
        # case: wrong type
        invalid_form = SelectCategoryProductForm(data={'category': 'not_category_type'})
        self.assertEqual(invalid_form.errors['category'], ['Select a valid choice. That choice is not one of the available choices.'])
        # case: inactive category
        self.category_2_2_2.is_active = False
        self.category_2_2_2.save()
        invalid_form = SelectCategoryProductForm(data={'category': self.category_2_2_2})
        self.assertEqual(invalid_form.errors['category'], ['Select a valid choice. That choice is not one of the available choices.'])



