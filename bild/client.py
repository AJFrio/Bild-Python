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
    project_users: "ProjectUsersAPI"
    branches_commits: "BranchesCommitsAPI"
    files: "FilesAPI"
    file_upload: "FileUploadAPI"
    file_checkin_checkout: "FileCheckinCheckoutAPI"
    shared_links: "SharedLinksAPI"
    files_move_delete: "FilesMoveDeleteAPI"
    files_metadata: "FilesMetadataAPI"
    feedback_items: "FeedbackItemsAPI"
    packages: "PackagesAPI"
    revisions: "RevisionsAPI"
    approvals: "ApprovalsAPI"
    boms: "BOMsAPI"
    search: "SearchAPI"


class BildClient:
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
            project_users=ProjectUsersAPI(self),
            branches_commits=BranchesCommitsAPI(self),
            files=FilesAPI(self),
            file_upload=FileUploadAPI(self),
            file_checkin_checkout=FileCheckinCheckoutAPI(self),
            shared_links=SharedLinksAPI(self),
            files_move_delete=FilesMoveDeleteAPI(self),
            files_metadata=FilesMetadataAPI(self),
            feedback_items=FeedbackItemsAPI(self),
            packages=PackagesAPI(self),
            revisions=RevisionsAPI(self),
            approvals=ApprovalsAPI(self),
            boms=BOMsAPI(self),
            search=SearchAPI(self),
        )

    def request(self, method: str, path: str, *, params=None, json=None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(
            method=method.upper(), url=url, params=params, json=json, timeout=self.timeout
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

    def resolve_branch_id(self, project_id: str, branch_id: str | None = None) -> str:
        if branch_id:
            return branch_id
        branches_payload = self.get(f"projects/{project_id}/branches")
        branches = _pick_list(branches_payload)
        if not branches:
            raise ValueError("No branches found for project and no branch_id provided")

        for b in branches:
            if not isinstance(b, dict):
                continue
            if b.get("isMain") or b.get("isDefault") or b.get("default"):
                return b.get("id") or b.get("branchId")
        for b in branches:
            if isinstance(b, dict) and str(b.get("name", "")).lower() in ("main", "master"):
                return b.get("id") or b.get("branchId")

        first = branches[0]
        if isinstance(first, dict):
            value = first.get("id") or first.get("branchId")
            if value:
                return value
        raise ValueError("Could not determine default branch_id")

    def resolve_file_version(
        self,
        project_id: str,
        branch_id: str,
        file_id: str,
        file_version: str | None = None,
    ) -> str:
        if file_version:
            return file_version
        latest = self.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/latestFileVersion")
        value = _pick_from_response(latest, "fileVersion", "id", "versionId", "latestFileVersion")
        if value:
            return str(value)
        raise ValueError("Could not determine file_version automatically")


class _BaseAPI:
    def __init__(self, client: BildClient):
        self.client = client


class UsersAPI(_BaseAPI):
    def list(self):
        return self.client.get("users")

    def add(self, emails: list[str], role: str = "Member", projects: list[dict] | None = None):
        return self.client.put("users/add", json={"emails": emails, "role": role, "projects": projects or []})


class ProjectsAPI(_BaseAPI):
    def list(self):
        return self.client.get("projects")


class ProjectUsersAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/users")

    def add(self, project_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/users", json=payload)

    def update(self, project_id: str, user_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/users/{user_id}", json=payload)


class BranchesCommitsAPI(_BaseAPI):
    def list_branches(self, project_id: str):
        return self.client.get(f"projects/{project_id}/branches")

    def branch(self, project_id: str, branch_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}")

    def commits(self, project_id: str, branch_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/commits")

    def commit(self, project_id: str, branch_id: str, commit_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/commits/{commit_id}")


class FilesAPI(_BaseAPI):
    def list(self, project_id: str, branch_id: str | None = None):
        if branch_id:
            return self.client.get(f"projects/{project_id}/branches/{branch_id}/files")
        return self.client.get(f"projects/{project_id}/files")

    def get(self, project_id: str, branch_id: str | None, file_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}")

    def latest_version(self, project_id: str, branch_id: str | None, file_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/latestFileVersion")

    def universal_format(
        self,
        project_id: str,
        branch_id: str | None,
        file_id: str,
        *,
        file_version: str | None,
        output_format: str,
    ):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        file_version = self.client.resolve_file_version(project_id, branch_id, file_id, file_version)
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/universalFormat",
            json={"fileVersion": file_version, "universalFileFormat": output_format},
        )


class FileUploadAPI(_BaseAPI):
    def init_upload(self, project_id: str, branch_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/fileUpload", json=payload)

    def complete_upload(self, project_id: str, branch_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/branches/{branch_id}/fileUpload", json=payload)


class FileCheckinCheckoutAPI(_BaseAPI):
    def checkout(self, project_id: str, branch_id: str, file_id: str, payload: dict | None = None):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/checkout", json=payload or {})

    def checkin(self, project_id: str, branch_id: str, file_id: str, payload: dict | None = None):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/checkin", json=payload or {})

    def discard_checkout(self, project_id: str, branch_id: str, file_id: str, payload: dict | None = None):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/discardCheckout", json=payload or {})

    def create_version(self, project_id: str, branch_id: str, file_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions", json=payload)


class SharedLinksAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/sharedLinks")

    def get(self, project_id: str, link_id: str):
        return self.client.get(f"projects/{project_id}/sharedLinks/{link_id}")

    def create(self, project_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/sharedLinks", json=payload)

    def update(self, project_id: str, link_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/sharedLinks/{link_id}", json=payload)


class FilesMoveDeleteAPI(_BaseAPI):
    def move(self, project_id: str, branch_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/move", json=payload)

    def delete_many(self, project_id: str, branch_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/delete", json=payload)


class FilesMetadataAPI(_BaseAPI):
    def fields(self):
        return self.client.get("metadataFields")

    def file_metadata(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/metadata")

    def update_file_metadata(self, project_id: str, branch_id: str, file_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/metadata", json=payload)


class FeedbackItemsAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/feedbackItems")

    def get(self, project_id: str, item_id: str):
        return self.client.get(f"projects/{project_id}/feedbackItems/{item_id}")

    def create(self, project_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/feedbackItems", json=payload)

    def update(self, project_id: str, item_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/feedbackItems/{item_id}", json=payload)

    def delete(self, project_id: str, item_id: str):
        return self.client.delete(f"projects/{project_id}/feedbackItems/{item_id}")


class PackagesAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/packages")

    def get(self, project_id: str, package_id: str):
        return self.client.get(f"projects/{project_id}/packages/{package_id}")


class RevisionsAPI(_BaseAPI):
    def list(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/revisions")

    def get(self, project_id: str, branch_id: str, file_id: str, revision_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/revisions/{revision_id}")

    def restore(self, project_id: str, branch_id: str, file_id: str, revision_id: str, payload: dict | None = None):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/revisions/{revision_id}/restore",
            json=payload or {},
        )


class ApprovalsAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/approvals")

    def get(self, project_id: str, approval_id: str):
        return self.client.get(f"projects/{project_id}/approvals/{approval_id}")

    def update(self, project_id: str, approval_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/approvals/{approval_id}", json=payload)


class BOMsAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/boms")

    def get(self, project_id: str, bom_id: str):
        return self.client.get(f"projects/{project_id}/boms/{bom_id}")

    def create(self, project_id: str, payload: dict):
        return self.client.post(f"projects/{project_id}/boms", json=payload)


class SearchAPI(_BaseAPI):
    def query(self, payload: dict):
        return self.client.put("search", json=payload)


def _pick_from_response(payload: Any, *keys: str):
    if isinstance(payload, dict):
        for k in keys:
            if k in payload and payload[k]:
                return payload[k]
        if isinstance(payload.get("data"), dict):
            return _pick_from_response(payload["data"], *keys)
    return None


def _pick_list(payload: Any):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("items"), list):
            return payload["items"]
    return []


def _safe_json(response: requests.Response):
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}
