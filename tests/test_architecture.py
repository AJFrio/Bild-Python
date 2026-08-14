from __future__ import annotations

import unittest

from bild import BildAPIError, BildAuthError, BildClient
from bild.client import _Resources
from tools.linters import check_architecture, check_docs_structure, check_taste


class TestPublicSurface(unittest.TestCase):
    def test_exports(self):
        import bild

        self.assertEqual(
            set(bild.__all__),
            {"BildClient", "BildAPIError", "BildAuthError"},
        )
        self.assertIs(bild.BildClient, BildClient)
        self.assertIs(bild.BildAPIError, BildAPIError)
        self.assertIs(bild.BildAuthError, BildAuthError)

    def test_resources_match_client(self):
        expected = {name for name in _Resources.__annotations__}
        client = BildClient(token="test-token")
        actual = {name for name in vars(client.api) if not name.startswith("_")}
        self.assertEqual(expected, actual)
        for name in expected:
            resource = getattr(client.api, name)
            self.assertTrue(
                type(resource).__name__.endswith("API"),
                f"{name} should be an *API class, got {type(resource).__name__}",
            )


class TestHarnessLinters(unittest.TestCase):
    def test_docs_structure(self):
        violations = check_docs_structure()
        self.assertEqual([], violations, "\n".join(v.format() for v in violations))

    def test_architecture(self):
        violations = check_architecture()
        self.assertEqual([], violations, "\n".join(v.format() for v in violations))

    def test_taste(self):
        violations = check_taste()
        self.assertEqual([], violations, "\n".join(v.format() for v in violations))


if __name__ == "__main__":
    unittest.main()
