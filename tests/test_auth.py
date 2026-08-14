from __future__ import annotations

import os
import sys
import types
import unittest
from dataclasses import dataclass
from urllib.parse import urlparse

try:
    import requests  # noqa: F401
except ImportError:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildAuthError, BildClient
from bild.client import DEFAULT_BASE_URL


@dataclass
class FakeResponse:
    status_code: int
    payload: dict

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self.payload

    @property
    def text(self):
        return str(self.payload)


class RecordingSession:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.headers = {}
        self.calls = []
        self.status_code = status_code
        self.payload = payload or {"ok": True}

    def request(self, method, url, params=None, json=None, timeout=None, **kwargs):
        self.calls.append(
            {
                "method": method.upper(),
                "url": url,
                "path": urlparse(url).path,
                "params": params,
                "json": json,
                "json_passed": "json" in kwargs or json is not None,
                "headers": dict(self.headers),
                "timeout": timeout,
            }
        )
        return FakeResponse(self.status_code, self.payload)


class TestBildAuth(unittest.TestCase):
    def test_missing_token_raises(self):
        env = os.environ.pop("BILD_API_KEY", None)
        try:
            with self.assertRaises(ValueError):
                BildClient(session=RecordingSession())
        finally:
            if env is not None:
                os.environ["BILD_API_KEY"] = env

    def test_bearer_header_and_default_host(self):
        session = RecordingSession()
        client = BildClient(token="jwt-token", session=session)
        self.assertEqual(DEFAULT_BASE_URL, "https://api.getbild.com")
        self.assertEqual(session.headers["Authorization"], "Bearer jwt-token")
        self.assertEqual(session.headers["Accept"], "application/json")
        self.assertNotIn("Content-Type", session.headers)
        self.assertTrue(client.base_url.startswith("https://api.getbild.com"))

    def test_get_does_not_send_json_body(self):
        session = RecordingSession()
        client = BildClient(token="jwt-token", session=session)
        client.api.users.list()
        call = session.calls[-1]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["path"], "/users")
        self.assertIsNone(call["json"])
        self.assertFalse(call["json_passed"])
        self.assertEqual(call["headers"]["Authorization"], "Bearer jwt-token")
        self.assertNotIn("Content-Type", call["headers"])

    def test_write_sends_json_payload(self):
        session = RecordingSession()
        client = BildClient(token="jwt-token", session=session)
        client.api.users.invite(["a@example.com"], projects=[])
        call = session.calls[-1]
        self.assertEqual(call["method"], "PUT")
        self.assertEqual(call["json"]["emails"], ["a@example.com"])
        self.assertTrue(call["json_passed"])

    def test_401_raises_auth_error(self):
        session = RecordingSession(status_code=401, payload={"message": "InvalidAuth"})
        client = BildClient(token="bad-token", session=session)
        with self.assertRaises(BildAuthError) as ctx:
            client.api.projects.list()
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.payload, {"message": "InvalidAuth"})

    def test_403_raises_auth_error(self):
        session = RecordingSession(status_code=403, payload={"message": "Forbidden"})
        client = BildClient(token="jwt-token", session=session)
        with self.assertRaises(BildAuthError):
            client.api.projects.list()

    def test_verify_lists_users_and_projects(self):
        session = RecordingSession()
        client = BildClient(token="jwt-token", session=session)
        result = client.verify()
        self.assertEqual(
            result,
            {
                "ok": True,
                "function": "BildClient.verify",
                "base_url": DEFAULT_BASE_URL,
                "users": {"ok": True},
                "projects": {"ok": True},
            },
        )
        paths = [call["path"] for call in session.calls]
        self.assertEqual(paths, ["/users", "/projects"])
        self.assertTrue(all(call["method"] == "GET" for call in session.calls))
        self.assertTrue(all(call["json"] is None for call in session.calls))


@unittest.skipUnless(os.getenv("BILD_API_KEY"), "BILD_API_KEY not set")
class TestLiveAuth(unittest.TestCase):
    def test_list_users_with_real_token(self):
        client = BildClient()
        result = client.api.users.list()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
