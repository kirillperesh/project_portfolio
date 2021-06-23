from django.test import TestCase, SimpleTestCase, Client, TransactionTestCase, client, tag
from django.urls import reverse, resolvers
from django.conf import settings
import importlib
import types, os
from django.contrib.auth.models import User



@tag('gitignore')
class AllUrlsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Collects all URLs from URLCONF
        Excludes all Virtual Env urls and native django urls
        Tests if all the patterns have names"""
        cls.urls_module = importlib.import_module(settings.ROOT_URLCONF)
        cls.env_path = os.environ['VIRTUAL_ENV'].lower()
        cls.urls_to_test = dict() # pattern - fullname pairs
        cls.patterns_to_test = list()

        cls.test_user_staff = User.objects.create(username='test_user_staff', is_staff=True)
        cls.test_user_superuser = User.objects.create(username='test_user_superuser', is_staff=True, is_superuser=True)

        for pattern in cls.urls_module.urlpatterns:
            if isinstance(pattern, resolvers.URLPattern):
                cls.patterns_to_test.append(pattern)
                continue
            if hasattr(pattern, 'urlconf_module'):
                if isinstance(pattern.urlconf_module, types.ModuleType) and not cls.env_path in pattern.urlconf_module.__file__.lower():
                    cls.patterns_to_test.append(pattern)

        def check_urls_names(urlpatterns, prefix=''):
            for pattern in urlpatterns:
                if hasattr(pattern, 'url_patterns'): # this is an included urlconf
                    new_prefix = prefix
                    if pattern.namespace:
                        new_prefix = prefix + (":" if prefix else "") + pattern.namespace
                    check_urls_names(pattern.url_patterns, prefix=new_prefix)
                else:
                    if hasattr(pattern, "name") and pattern.name:
                        fullname = (prefix + ":" + pattern.name) if prefix else pattern.name
                    else:
                        fullname = None
                    cls.urls_to_test[pattern] = fullname
        check_urls_names(cls.patterns_to_test)

    def test_urls_names(self):
        for url, name in self.urls_to_test.items():
            self.assertIsNotNone(name, f'\nPattern {url} has no name')

    def test_responses(self, allowed_http_codes=[200, 302, 405], logout_url=reverse('logout'), default_kwargs={}, quiet=True):
        """
        Test all patterns in root urlconf and included ones.
        Do GET requests only.
        A pattern is skipped if any of the conditions applies:
            - pattern has no name in urlconf
            - pattern expects any positinal parameters
            - pattern expects keyword parameters that are not specified in @default_kwargs
        If response code is not in @allowed_http_codes, fail the test.
        If @logout_url is specified, then check if we accidentally logged out
            the client while testing, and login again
        Specify @default_kwargs to be used for patterns that expect keyword parameters,
            e.g. if you specify default_kwargs={'username': 'testuser'}, then
            for pattern url(r'^accounts/(?P<username>[\.\w-]+)/$'
            the url /accounts/testuser/ will be tested.
        If @quiet=False, print all the urls checked. If status code of the response is not 200,
            print the status code.
        """

        for pattern, name in self.urls_to_test.items():
            params = {}
            regex = pattern.pattern.regex
            if regex.groups > 0:
                # the url expects parameters
                # use default_kwargs supplied
                if regex.groups > len(regex.groupindex.keys()) \
                    or set(regex.groupindex.keys()) - set(default_kwargs.keys()):
                    # there are positional parameters OR
                    # keyword parameters that are not supplied in default_kwargs
                    # so we skip the url
                    if not quiet:
                        print("SKIPPED " + regex.pattern + " " + name)
                    continue
                else:
                    for key in set(default_kwargs.keys()) & set(regex.groupindex.keys()):
                        params[key] = default_kwargs[key]
            url = reverse(name, kwargs=params)
            response = self.client.get(url)
            if response.status_code in [403, 404, 500]: # check staff only permission
                self.client.force_login(self.test_user_staff)
                response = self.client.get(url)
                if not quiet and response.status_code in allowed_http_codes: print("STAFF ONLY" + regex.pattern + " " + name)
                if response.status_code in [403, 404, 500]: # check superuser only permission
                    self.client.force_login(self.test_user_superuser)
                    response = self.client.get(url)
                    if not quiet and response.status_code in allowed_http_codes: print("SUPERUSER ONLY" + regex.pattern + " " + name)

            self.assertIn(response.status_code, allowed_http_codes)
            # print status code if it is not 200
            status = "" if response.status_code == 200 else str(response.status_code)
            if not quiet:
                print(status + ' ' + url)

class BasicUrlsTest(TestCase):
    """
    Tests a list of URLs
    If @quiet=False, print all the urls checked. If status code of the response is not 200, print the status code.
    """
    def test_basic_urls(self, allowed_http_codes=[200, 302, 405], named_urls = ['home', 'sign_in', 'sign_up', 'logout'], quiet=True):
        for named_url in named_urls:
            response = self.client.get(reverse(named_url))
            self.assertIn(response.status_code, allowed_http_codes)
            if not quiet:
                status = "" if response.status_code == 200 else str(response.status_code)
                print(status + ' ' + named_url)
