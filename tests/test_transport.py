from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import requests  # noqa: F401
except ImportError:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildAPIError, BildAuthError, BildClient
from bild.client import _load_env_file, _safe_json
from tests.fakes import FakeResponse, RecordingSession


class TestTransport(unittest.TestCase):
    def test_constructor_token_wins_over_env(self):
        previous = os.environ.get("BILD_API_KEY")
        os.environ["BILD_API_KEY"] = "env-token"
        try:
            session = RecordingSession()
            BildClient(token="ctor-token", session=session)
            self.assertEqual(session.headers["Authorization"], "Bearer ctor-token")
        finally:
            if previous is None:
                os.environ.pop("BILD_API_KEY", None)
            else:
                os.environ["BILD_API_KEY"] = previous

    def test_custom_base_url_and_timeout(self):
        session = RecordingSession()
        client = BildClient(
            token="jwt-token",
            base_url="https://example.test/api/",
            timeout=12.5,
            session=session,
        )
        client.api.users.list()
        call = session.calls[-1]
        self.assertEqual(call["url"], "https://example.test/api/users")
        self.assertEqual(call["timeout"], 12.5)

    def test_404_raises_api_error_not_auth(self):
        session = RecordingSession(status_code=404, payload={"message": "missing"})
        client = BildClient(token="jwt-token", session=session)
        with self.assertRaises(BildAPIError) as ctx:
            client.api.projects.list()
        self.assertNotIsInstance(ctx.exception, BildAuthError)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.payload, {"message": "missing"})

    def test_500_raises_api_error(self):
        session = RecordingSession(status_code=500, payload={"message": "boom"})
        client = BildClient(token="jwt-token", session=session)
        with self.assertRaises(BildAPIError) as ctx:
            client.api.projects.list()
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(ctx.exception.payload, {"message": "boom"})

    def test_delete_does_not_send_json_body(self):
        session = RecordingSession()
        client = BildClient(token="jwt-token", session=session)
        client.api.webhooks.delete("sub1")
        call = session.calls[-1]
        self.assertEqual(call["method"], "DELETE")
        self.assertEqual(call["path"], "/webhooks/subscriptions/sub1")
        self.assertIsNone(call["json"])
        self.assertFalse(call["json_passed"])
        self.assertNotIn("Content-Type", call["headers"])

    def test_empty_204_returns_none(self):
        session = RecordingSession(status_code=204, empty=True)
        client = BildClient(token="jwt-token", session=session)
        result = client.api.webhooks.delete("sub1")
        self.assertIsNone(result)

    def test_non_json_body_returns_raw(self):
        response = FakeResponse(status_code=200, payload=None, raw_text="<html>nope</html>")
        self.assertEqual(_safe_json(response), {"raw": "<html>nope</html>"})

    def test_empty_body_returns_none(self):
        response = FakeResponse(status_code=204, payload=None)
        self.assertIsNone(_safe_json(response))

    def test_env_file_does_not_override_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("BILD_SDK_ENV_LOAD_TEST=from-file\n", encoding="utf-8")
            with patch.dict(os.environ, {"BILD_SDK_ENV_LOAD_TEST": "from-process"}):
                with patch("bild.client.Path.cwd", return_value=Path(tmp)):
                    _load_env_file()
                self.assertEqual(os.environ["BILD_SDK_ENV_LOAD_TEST"], "from-process")

    def test_env_file_sets_missing_key(self):
        previous = os.environ.pop("BILD_SDK_ENV_LOAD_TEST", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                env_path = Path(tmp) / ".env"
                env_path.write_text("BILD_SDK_ENV_LOAD_TEST=from-file\n", encoding="utf-8")
                with patch("bild.client.Path.cwd", return_value=Path(tmp)):
                    _load_env_file()
                self.assertEqual(os.environ["BILD_SDK_ENV_LOAD_TEST"], "from-file")
        finally:
            if previous is None:
                os.environ.pop("BILD_SDK_ENV_LOAD_TEST", None)
            else:
                os.environ["BILD_SDK_ENV_LOAD_TEST"] = previous


if __name__ == "__main__":
    unittest.main()
