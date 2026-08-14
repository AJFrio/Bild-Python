from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass
class FakeResponse:
    status_code: int = 200
    payload: Any = None
    raw_text: str | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content(self) -> bytes:
        if self.raw_text is not None:
            return self.raw_text.encode("utf-8")
        if self.payload is None:
            return b""
        return b"{}"

    @property
    def text(self) -> str:
        if self.raw_text is not None:
            return self.raw_text
        if self.payload is None:
            return ""
        return str(self.payload)

    def json(self) -> Any:
        if self.payload is None:
            raise ValueError("No JSON body")
        return self.payload


class RecordingSession:
    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        *,
        empty: bool = False,
    ):
        self.headers: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []
        self.status_code = status_code
        if empty:
            self.payload = None
        else:
            self.payload = {"ok": True} if payload is None else payload

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
        return FakeResponse(self.status_code, payload=self.payload)


class ScriptedSession:
    def __init__(self, by_suffix: dict[str, FakeResponse] | None = None):
        self.headers: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []
        self.by_suffix = by_suffix or {}

    def request(self, method, url, params=None, json=None, timeout=None, **kwargs):
        path = urlparse(url).path
        self.calls.append(
            {
                "method": method.upper(),
                "url": url,
                "path": path,
                "json": json,
                "params": params,
                "timeout": timeout,
            }
        )
        for suffix, response in self.by_suffix.items():
            if path.endswith(suffix):
                return response
        return FakeResponse(200, {"ok": True, "path": path})


class RouteSession(ScriptedSession):
    def __init__(self):
        super().__init__(
            {
                "/branches": FakeResponse(200, {"data": [{"id": "branch-main", "isMain": True}]}),
                "/latest": FakeResponse(200, {"data": {"fileVersion": "v-latest"}}),
            }
        )
