from __future__ import annotations

import sys
import types
import unittest

try:
    import requests  # noqa: F401
except ImportError:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildClient
from tests.fakes import FakeResponse, RecordingSession, ScriptedSession


class TestResolveBranchId(unittest.TestCase):
    def _client(self, payload) -> BildClient:
        session = ScriptedSession({"/branches": FakeResponse(200, payload)})
        return BildClient(token="test-token", session=session)

    def test_explicit_id_skips_lookup(self):
        session = RecordingSession()
        client = BildClient(token="test-token", session=session)
        self.assertEqual(client.resolve_branch_id("p1", "given"), "given")
        self.assertEqual(session.calls, [])

    def test_prefers_is_main(self):
        client = self._client(
            {
                "data": [
                    {"id": "other", "name": "dev"},
                    {"id": "main-id", "isMain": True},
                ]
            }
        )
        self.assertEqual(client.resolve_branch_id("p1"), "main-id")

    def test_prefers_is_default(self):
        client = self._client({"data": [{"id": "def-id", "isDefault": True}]})
        self.assertEqual(client.resolve_branch_id("p1"), "def-id")

    def test_prefers_default_flag(self):
        client = self._client({"items": [{"id": "flag-id", "default": True}]})
        self.assertEqual(client.resolve_branch_id("p1"), "flag-id")

    def test_falls_back_to_name_main(self):
        client = self._client({"data": [{"id": "named", "name": "Main"}]})
        self.assertEqual(client.resolve_branch_id("p1"), "named")

    def test_falls_back_to_name_master(self):
        client = self._client({"data": [{"branchId": "master-id", "name": "master"}]})
        self.assertEqual(client.resolve_branch_id("p1"), "master-id")

    def test_falls_back_to_first_branch(self):
        client = self._client({"data": [{"id": "only"}]})
        self.assertEqual(client.resolve_branch_id("p1"), "only")

    def test_empty_list_raises(self):
        client = self._client({"data": []})
        with self.assertRaises(ValueError):
            client.resolve_branch_id("p1")

    def test_missing_ids_raise(self):
        client = self._client({"data": [{"name": "main"}, "skip-me"]})
        with self.assertRaises(ValueError):
            client.resolve_branch_id("p1")


class TestResolveFileVersion(unittest.TestCase):
    def test_explicit_version_skips_lookup(self):
        session = RecordingSession()
        client = BildClient(token="test-token", session=session)
        self.assertEqual(
            client.resolve_file_version("p1", "b1", "f1", "v-given"),
            "v-given",
        )
        self.assertEqual(session.calls, [])

    def test_reads_nested_file_version(self):
        session = ScriptedSession(
            {"/latest": FakeResponse(200, {"data": {"fileVersion": "v-latest"}})}
        )
        client = BildClient(token="test-token", session=session)
        self.assertEqual(client.resolve_file_version("p1", "b1", "f1"), "v-latest")

    def test_reads_file_version_id(self):
        session = ScriptedSession({"/latest": FakeResponse(200, {"fileVersionID": "v-id"})})
        client = BildClient(token="test-token", session=session)
        self.assertEqual(client.resolve_file_version("p1", "b1", "f1"), "v-id")

    def test_missing_version_raises(self):
        session = ScriptedSession({"/latest": FakeResponse(200, {"data": {}})})
        client = BildClient(token="test-token", session=session)
        with self.assertRaises(ValueError):
            client.resolve_file_version("p1", "b1", "f1")


if __name__ == "__main__":
    unittest.main()
