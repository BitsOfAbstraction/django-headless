import sys
from unittest.mock import patch

from django.test import SimpleTestCase

from headless.registry import HeadlessRegistry
from headless.settings import headless_settings
from headless.utils import is_jsonable, flatten, is_runserver


class UtilsTests(SimpleTestCase):
    def test_is_jsonable(self):
        self.assertTrue(is_jsonable({"a": 1}))
        self.assertTrue(is_jsonable([1, 2, 3]))
        self.assertFalse(is_jsonable(set([1, 2, 3])))

    def test_flatten(self):
        self.assertEqual(flatten([[1, 2], [3], [], [4, 5]]), [1, 2, 3, 4, 5])

    def test_is_runserver_with_runserver(self):
        with patch.object(sys, "argv", ["/path/manage.py", "runserver"]):
            self.assertTrue(is_runserver())

    def test_is_runserver_with_runserver_plus(self):
        with patch.object(sys, "argv", ["/path/manage.py", "runserver_plus"]):
            self.assertTrue(is_runserver())

    def test_is_runserver_with_migrate(self):
        with patch.object(sys, "argv", ["/path/manage.py", "migrate"]):
            self.assertFalse(is_runserver())

    def test_is_runserver_with_wsgi(self):
        with patch.object(sys, "argv", ["/path/wsgi.py"]):
            self.assertTrue(is_runserver())

    def test_is_runserver_with_empty_args(self):
        with patch.object(sys, "argv", []):
            self.assertFalse(is_runserver())

    def test_is_runserver_with_insufficient_args(self):
        with patch.object(sys, "argv", ["/path/manage.py"]):
            self.assertFalse(is_runserver())


class SettingsTests(SimpleTestCase):
    def test_defaults_available(self):
        # Ensure default settings are accessible and of expected types
        self.assertIsNone(headless_settings.AUTH_SECRET_KEY)
        self.assertIsInstance(headless_settings.AUTH_SECRET_KEY_HEADER, str)
        self.assertIsInstance(headless_settings.FILTER_EXCLUSION_SYMBOL, str)
        self.assertIsInstance(headless_settings.NON_FILTER_FIELDS, list)
        # DEFAULT_SERIALIZER_CLASS resolves to a class
        from rest_framework.serializers import ModelSerializer

        self.assertTrue(
            issubclass(headless_settings.DEFAULT_SERIALIZER_CLASS, ModelSerializer)
        )


class RegistryTests(SimpleTestCase):
    def test_registry_register_and_get(self):
        # Create a fake model class with minimal _meta interface
        class _Meta:
            label_lower = "app.model"
            fields = []

        class FakeModel:
            _meta = _Meta()

        reg = HeadlessRegistry()
        reg.register(FakeModel, singleton=True)
        self.assertEqual(len(reg), 1)
        cfg = reg.get_model("APP.Model")
        self.assertIsNotNone(cfg)
        self.assertIs(cfg["model"], FakeModel)
        self.assertTrue(cfg["singleton"])
