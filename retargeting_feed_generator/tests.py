import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from .views import index
        request = testing.DummyRequest()
        info = index(request)
        self.assertEqual(info['project'], 'retargeting_feed_generator')


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from retargeting_feed_generator import main
        app = main({})
        from webtest import TestApp
        self.testapp = TestApp(app)

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue(b'Pyramid' in res.body)
