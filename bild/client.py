from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

from .errors import BildAPIError, BildAuthError


DEFAULT_BASE_URL = "https://api.portle.io/api"


@dataclass
class _Resources:
    users: "UsersAPI"
    projects: "ProjectsAPI"
    files: "FilesAPI"
    metadata: "MetadataAPI"
    search: "SearchAPI"


class BildClient:
    """SDK client for the Bild External API."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.token = token or os.getenv("BILD_API_KEY")
        if not self.token:
            raise ValueError("Missing token. Pass token=... or set BILD_API_KEY")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        self.api = _Resources(
            users=UsersAPI(self),
            projects=ProjectsAPI(self),
            files=FilesAPI(self),
            metadata=MetadataAPI(self),
            search=SearchAPI(self),
        )

    def request(self, method: str, path: str, *, params=None, json=None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            timeout=self.timeout,
        )

        if response.status_code in (401, 403):
            raise BildAuthError(
                "Authentication/authorization failed",
                status_code=response.status_code,
                payload=_safe_json(response),
            )

        if not response.ok:
            raise BildAPIError(
                f"API error {response.status_code}",
                status_code=response.status_code,
                payload=_safe_json(response),
            )

        return _safe_json(response)

    def get(self, path: str, *, params=None):
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json=None, params=None):
        return self.request("POST", path, params=params, json=json)

    def put(self, path: str, *, json=None, params=None):
        return self.request("PUT", path, params=params, json=json)

    def delete(self, path: str, *, params=None):
        return self.request("DELETE", path, params=params)


class UsersAPI:
    def __init__(self, client: BildClient):
        self.client = client

    def list(self):
        return self.client.get("users")

    def add(self, emails: list[str], role: str = "Member", projects: list[dict] | None = None):
        if not emails:
            raise ValueError("emails cannot be empty")
        return self.client.put(
            "users/add",
            json={"emails": emails, "role": role, "projects": projects or []},
        )


class ProjectsAPI:
    def __init__(self, client: BildClient):
        self.client = client

    def list(self):
        return self.client.get("projects")

    def users(self, project_id: str):
        return self.client.get(f"projects/{project_id}/users")

    def files(self, project_id: str):
        return self.client.get(f"projects/{project_id}/files")


class FilesAPI:
    def __init__(self, client: BildClient):
        self.client = client

    def latest_version(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/latestFileVersion"
        )

    def universal_format(
        self,
        project_id: str,
        branch_id: str,
        file_id: str,
        *,
        file_version: str,
        output_format: str,
    ):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/universalFormat",
            json={"fileVersion": file_version, "universalFileFormat": output_format},
        )

    def to_stl(self, project_id: str, branch_id: str, file_id: str, *, file_version: str):
        return self.universal_format(
            project_id,
            branch_id,
            file_id,
            file_version=file_version,
            output_format="stl",
        )

    def to_step(self, project_id: str, branch_id: str, file_id: str, *, file_version: str):
        return self.universal_format(
            project_id,
            branch_id,
            file_id,
            file_version=file_version,
            output_format="step",
        )


class MetadataAPI:
    def __init__(self, client: BildClient):
        self.client = client

    def fields(self):
        return self.client.get("metadataFields")

    def file_metadata(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/metadata")


class SearchAPI:
    def __init__(self, client: BildClient):
        self.client = client

    def query(self, payload: dict):
        return self.client.put("search", json=payload)


def _safe_json(response: requests.Response):
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}
