import sys
import types

try:
    import requests  # noqa: F401
except ImportError:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildClient


def test_import():
    assert BildClient is not None
