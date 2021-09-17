from django.test import TestCase
from django.utils.crypto import get_random_string
from urllib.parse import quote_plus
import random

from glyke_back.templatetags import glyke_back_extras as extras


class TestExtraTemplateTags(TestCase):
    """
    TODO"""

    @classmethod
    def setUpTestData(cls):
        cls.every_symbol_string = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'

    def setUp(self):
        self.rnd_string_1 = ' ' + get_random_string(length=20) + ' '
        self.rnd_string_2 = ' ' + get_random_string(length=20) + ' '
        self.rnd_int_1 = random.randint(101, 199)

    def test_addstr(self):
        """
        TODO"""
        actual_result = extras.addstr(self.rnd_string_1, self.rnd_int_1)
        expected_result = self.rnd_string_1 + str(self.rnd_int_1)
        self.assertEqual(expected_result, actual_result)

    def test_remove_first_occ_substr(self):
        """
        TODO"""
        test_concat_str = self.rnd_string_1 + self.rnd_string_2 + self.rnd_string_2
        actual_result = extras.remove_first_occ_substr(test_concat_str, self.rnd_string_2)
        expected_result = self.rnd_string_1 + self.rnd_string_2
        self.assertEqual(expected_result, actual_result)

    def test_append_url_param_value(self):
        """
        TODO"""
        test_url_param_name = 'test_param='
        actual_result = extras.append_url_param_value(test_url_param_name, self.every_symbol_string)
        expected_result = test_url_param_name + quote_plus(self.every_symbol_string, encoding='utf-8')
        self.assertEqual(expected_result, actual_result)

    def test_remove_all_occ_url_param(self):
        """
        TODO"""
        test_urls_params = '&test_param_1=test_value_1&test_param_2=test_value_2&test_param_1=test_value_3&test_param_2=test_value_4&'
        assert_results_map = {'no_such_test_param':test_urls_params,
                              'test_param_1':'test_param_2=test_value_2&test_param_2=test_value_4',
                              'test_param_2':'test_param_1=test_value_1&test_param_1=test_value_3',
                              'test_param_':'',}
        for test_param, expected_result in assert_results_map.items():
            actual_result = extras.remove_all_occ_url_param(test_urls_params, test_param)
            self.assertEqual(expected_result, actual_result)









