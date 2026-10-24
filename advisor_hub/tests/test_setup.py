"""Import smoke tests that do not require the optional interface dependency."""

import importlib
import unittest


class ImportTests(unittest.TestCase):
    def test_classifier_import(self):
        module = importlib.import_module("advisor_hub.classifier")
        self.assertTrue(callable(module.classify_request))

    def test_interface_import(self):
        module = importlib.import_module("advisor_hub.app")
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
