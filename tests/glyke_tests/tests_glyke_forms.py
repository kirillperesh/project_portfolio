from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from glyke_back.models import *
from glyke_back.forms import *


class AddProductFormATest(TestCase):
    pass

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

    def test_fields_count(self):
        """Checks if the form return correct fields"""
        self.assertListEqual(list(self.test_form.fields.keys()), ['category',])

    def test_choices_count(self):
        """Checks if the form return correct number of choices"""
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



