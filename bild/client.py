from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .errors import BildAPIError, BildAuthError

DEFAULT_BASE_URL = "https://api.getbild.com"


def _load_env_file() -> None:
    """Load KEY=VALUE pairs from a local .env without overwriting existing env vars."""
    candidates = [Path.cwd() / ".env"]
    try:
        candidates.append(Path(__file__).resolve().parents[1] / ".env")
    except IndexError:
        pass

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()


@dataclass
class _Resources:
    users: UsersAPI
    projects: ProjectsAPI
    project_users: ProjectUsersAPI
    branches: BranchesAPI
    commits: CommitsAPI
    files: FilesAPI
    uploads: UploadsAPI
    checkouts: CheckoutsAPI
    shared_links: SharedLinksAPI
    metadata: MetadataAPI
    feedback: FeedbackAPI
    packages: PackagesAPI
    revisions: RevisionsAPI
    approvals: ApprovalsAPI
    boms: BOMsAPI
    search: SearchAPI
    webhooks: WebhooksAPI


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
        # Do not set Content-Type on the session. Bild's API treats that header as
        # "this request has a JSON body" and GET/DELETE calls then 500 with
        # "Unexpected end of JSON input". requests sets Content-Type when json= is used.
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            }
        )

        self.api = _Resources(
            users=UsersAPI(self),
            projects=ProjectsAPI(self),
            project_users=ProjectUsersAPI(self),
            branches=BranchesAPI(self),
            commits=CommitsAPI(self),
            files=FilesAPI(self),
            uploads=UploadsAPI(self),
            checkouts=CheckoutsAPI(self),
            shared_links=SharedLinksAPI(self),
            metadata=MetadataAPI(self),
            feedback=FeedbackAPI(self),
            packages=PackagesAPI(self),
            revisions=RevisionsAPI(self),
            approvals=ApprovalsAPI(self),
            boms=BOMsAPI(self),
            search=SearchAPI(self),
            webhooks=WebhooksAPI(self),
        )

    def verify(self) -> dict[str, Any]:
        """Read-only setup handshake used by AGENT_SETUP.md.

        Lists users and projects so an installing agent can prove the token
        works and show the human the exact return value.
        """
        return {
            "ok": True,
            "function": "BildClient.verify",
            "base_url": self.base_url,
            "users": self.api.users.list(),
            "projects": self.api.projects.list(),
        }

    def request(self, method: str, path: str, *, params=None, json=None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        kwargs: dict[str, Any] = {
            "method": method.upper(),
            "url": url,
            "params": params,
            "timeout": self.timeout,
        }
        if json is not None:
            kwargs["json"] = json
        response = self.session.request(**kwargs)
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
                value = b.get("id") or b.get("branchId")
                if value:
                    return str(value)
        for b in branches:
            if isinstance(b, dict) and str(b.get("name", "")).lower() in ("main", "master"):
                value = b.get("id") or b.get("branchId")
                if value:
                    return str(value)

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
        latest = self.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/latest")
        value = _pick_from_response(
            latest, "fileVersion", "fileVersionID", "id", "versionId", "latestFileVersion"
        )
        if value:
            return str(value)
        raise ValueError("Could not determine file_version automatically")


class _BaseAPI:
    def __init__(self, client: BildClient):
        self.client = client


class UsersAPI(_BaseAPI):
    def list(self):
        return self.client.get("users")

    def invite(
        self,
        emails: Sequence[str],
        projects: Sequence[dict] | None = None,
        *,
        company_role: str | None = None,
        pdm_role: str | None = None,
        plm_role: str | None = None,
    ):
        return self.client.put(
            "users/add",
            json=_omit_none(
                {
                    "emails": emails,
                    "projects": projects or [],
                    "companyRole": company_role,
                    "pdmRole": pdm_role,
                    "plmRole": plm_role,
                }
            ),
        )

    def remove(self, user_ids: Sequence[str]):
        return self.client.put("users/remove", json={"userIDs": user_ids})

    def update(
        self,
        user_ids: Sequence[str],
        projects: Sequence[dict] | None = None,
        *,
        company_role: str | None = None,
        pdm_role: str | None = None,
        plm_role: str | None = None,
    ):
        return self.client.put(
            "users/update",
            json=_omit_none(
                {
                    "userIDs": user_ids,
                    "projects": projects or [],
                    "companyRole": company_role,
                    "pdmRole": pdm_role,
                    "plmRole": plm_role,
                }
            ),
        )

    def create_token(self, *, name: str | None = None, expiry: float | None = None):
        return self.client.post("users/apiToken", json=_omit_none({"name": name, "expiry": expiry}))


class ProjectsAPI(_BaseAPI):
    def list(self):
        return self.client.get("projects")


class ProjectUsersAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/users")

    def add(self, users: Sequence[dict], project_ids: Sequence[str] | None = None):
        return self.client.post(
            "projects/users/add",
            json=_omit_none({"users": users, "projectIDs": project_ids}),
        )

    def remove(self, project_ids: Sequence[str], user_ids: Sequence[str]):
        return self.client.put(
            "projects/users/remove",
            json={"projectIDs": project_ids, "userIDs": user_ids},
        )

    def update(self, users: Sequence[dict], project_ids: Sequence[str] | None = None):
        return self.client.put(
            "projects/users/update",
            json=_omit_none({"users": users, "projectIDs": project_ids}),
        )


class BranchesAPI(_BaseAPI):
    def list(self, project_id: str):
        return self.client.get(f"projects/{project_id}/branches")


class CommitsAPI(_BaseAPI):
    def list(self, project_id: str, branch_id: str | None = None):
        if branch_id:
            return self.client.get(f"projects/{project_id}/branches/{branch_id}/commits")
        return self.client.get(f"projects/{project_id}/commits")

    def get(self, project_id: str, branch_id: str, commit_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/commits/{commit_id}")


class FilesAPI(_BaseAPI):
    def list(self, project_id: str, branch_id: str | None = None):
        if branch_id:
            return self.client.get(f"projects/{project_id}/branches/{branch_id}/files")
        return self.client.get(f"projects/{project_id}/files")

    def list_released(self, from_time: str):
        return self.client.get("files/released", params={"fromTime": from_time})

    def list_versions(self, project_id: str, branch_id: str | None, file_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions"
        )

    def get_latest(self, project_id: str, branch_id: str | None, file_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/files/{file_id}/latest")

    def get_released(self, project_id: str, branch_id: str | None, file_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/released"
        )

    def get_version(self, project_id: str, branch_id: str | None, file_id: str, version_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions/{version_id}"
        )

    def get_thumbnail(self, project_id: str, branch_id: str | None, file_id: str, version_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions/{version_id}/thumbnail"
        )

    def get_children(self, project_id: str, branch_id: str | None, file_id: str, version_id: str):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions/{version_id}/children"
        )

    def export_universal(
        self,
        project_id: str,
        branch_id: str | None,
        file_id: str,
        *,
        output_format: str,
        file_version: str | None = None,
        file_config: str | None = None,
    ):
        branch_id = self.client.resolve_branch_id(project_id, branch_id)
        file_version = self.client.resolve_file_version(
            project_id, branch_id, file_id, file_version
        )
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/{file_id}/universalFormat",
            json=_omit_none(
                {
                    "fileVersionID": file_version,
                    "universalFileFormat": output_format,
                    "fileConfig": file_config,
                }
            ),
        )

    def export_universal_many(self, project_id: str, branch_id: str, payload: dict):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/files/exportUniversalFiles",
            json=payload,
        )

    def move(self, project_id: str, branch_id: str, file_ids: Sequence[str], new_parent_id: str):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/move",
            json={"moveFiles": file_ids, "newParentID": new_parent_id},
        )

    def delete(self, project_id: str, branch_id: str, file_ids: Sequence[str]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/delete",
            json={"fileIDs": file_ids},
        )


class UploadsAPI(_BaseAPI):
    def initiate(self, project_id: str, branch_id: str, files: Sequence[dict]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/initiateUpload",
            json={"files": files},
        )

    def complete(
        self,
        project_id: str,
        branch_id: str,
        files: Sequence[dict],
        *,
        keep_checked_out: bool | None = None,
    ):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/fileActions/completeUpload",
            json=_omit_none({"files": files, "keepFilesCheckedOut": keep_checked_out}),
        )


class CheckoutsAPI(_BaseAPI):
    def checkout(self, project_id: str, branch_id: str, file_ids: Sequence[str]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/checkout",
            json={"fileIDs": file_ids},
        )

    def cancel(self, project_id: str, branch_id: str, file_ids: Sequence[str]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/cancelCheckout",
            json={"fileIDs": file_ids},
        )

    def initiate_checkin(self, project_id: str, branch_id: str, files: Sequence[dict]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/fileActions/initiateCheckin",
            json={"files": files},
        )

    def complete_checkin(
        self,
        project_id: str,
        branch_id: str,
        files: Sequence[dict],
        *,
        message: str | None = None,
    ):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/fileActions/completeCheckin",
            json=_omit_none({"files": files, "message": message}),
        )


class SharedLinksAPI(_BaseAPI):
    def list(self, project_id: str | None = None, branch_id: str | None = None):
        if project_id and branch_id:
            return self.client.get(f"projects/{project_id}/branches/{branch_id}/sharedLinks")
        if project_id:
            return self.client.get(f"projects/{project_id}/sharedLinks")
        return self.client.get("sharedLinks")

    def create_live(
        self,
        project_id: str,
        branch_id: str,
        name: str,
        file_ids: Sequence[str],
        *,
        types: Sequence[str] | None = None,
        config_map: dict | None = None,
    ):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/files/sharedLink",
            json=_omit_none(
                {
                    "name": name,
                    "fileIDs": file_ids,
                    "types": types,
                    "configMap": config_map,
                }
            ),
        )

    def create_static(
        self,
        project_id: str,
        branch_id: str,
        file_id: str,
        version_id: str,
        payload: dict | None = None,
    ):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/fileVersion/{version_id}/sharedLink",
            json=payload or {},
        )

    def refresh(self, project_id: str, branch_id: str, link_id: str):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/sharedLinks/{link_id}/refresh"
        )

    def delete(self, project_id: str, branch_id: str, link_ids: Sequence[str]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/sharedLinks/delete",
            json={"sharedLinkIDs": link_ids},
        )


class MetadataAPI(_BaseAPI):
    def list_fields(self):
        return self.client.get("metadataFields")

    def get(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/metadata"
        )

    def get_for_version(self, project_id: str, branch_id: str, file_id: str, version_id: str):
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/versions/{version_id}/metadata"
        )

    def update(self, project_id: str, branch_id: str, payload: dict):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/files/updateMetadata",
            json=payload,
        )


class FeedbackAPI(_BaseAPI):
    def list(self, project_id: str, *, branch_id: str | None = None, file_id: str | None = None):
        if file_id:
            branch_id = self.client.resolve_branch_id(project_id, branch_id)
            return self.client.get(
                f"projects/{project_id}/branches/{branch_id}/files/{file_id}/feedbackItems"
            )
        return self.client.get(f"projects/{project_id}/feedbackItems")

    def get(self, project_id: str, item_id: str):
        return self.client.get(f"projects/{project_id}/feedbackItems/{item_id}")

    def update(self, project_id: str, item_id: str, payload: dict):
        return self.client.put(f"projects/{project_id}/feedbackItems/{item_id}", json=payload)

    def initiate_attachment(self, project_id: str, item_id: str, payload: dict):
        return self.client.put(
            f"projects/{project_id}/feedbackItems/{item_id}/attachment",
            json=payload,
        )

    def complete_attachment(
        self,
        project_id: str,
        item_id: str,
        attachment_id: str,
        payload: dict | None = None,
    ):
        return self.client.post(
            f"projects/{project_id}/feedbackItems/{item_id}/attachment/{attachment_id}",
            json=payload or {},
        )

    def delete_attachment(self, project_id: str, item_id: str, attachment_id: str):
        return self.client.delete(
            f"projects/{project_id}/feedbackItems/{item_id}/attachment/{attachment_id}"
        )


class PackagesAPI(_BaseAPI):
    def list(self, project_id: str | None = None):
        if project_id:
            return self.client.get(f"projects/{project_id}/packages")
        return self.client.get("packages")

    def get(self, project_id: str, package_id: str):
        return self.client.get(f"projects/{project_id}/packages/{package_id}")


class RevisionsAPI(_BaseAPI):
    def list(
        self,
        project_id: str | None = None,
        branch_id: str | None = None,
        file_id: str | None = None,
    ):
        if file_id:
            if not project_id or not branch_id:
                raise ValueError(
                    "project_id and branch_id are required when listing file revisions"
                )
            return self.client.get(
                f"projects/{project_id}/branches/{branch_id}/files/{file_id}/revisions"
            )
        if branch_id:
            if not project_id:
                raise ValueError("project_id is required when listing branch revisions")
            return self.client.get(f"projects/{project_id}/branches/{branch_id}/revisions")
        if project_id:
            return self.client.get(f"projects/{project_id}/revisions")
        return self.client.get("revisions")

    def get(self, project_id: str, branch_id: str, file_id: str, revision_id: str):
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/revisions/{revision_id}"
        )

    def get_closure(self, project_id: str, branch_id: str, file_id: str):
        return self.client.get(
            f"projects/{project_id}/branches/{branch_id}/files/{file_id}/closure"
        )

    def release(self, project_id: str, branch_id: str, revisions: Sequence[dict]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/revisions/release",
            json=revisions,
        )

    def cancel(self, project_id: str, branch_id: str, revision_ids: Sequence[str]):
        return self.client.put(
            f"projects/{project_id}/branches/{branch_id}/revisions/cancel",
            json={"revisionIDs": revision_ids},
        )


class ApprovalsAPI(_BaseAPI):
    def list(self, project_id: str | None = None):
        if project_id:
            return self.client.get(f"projects/{project_id}/approvals")
        return self.client.get("approvals")

    def get(self, project_id: str, approval_id: str):
        return self.client.get(f"projects/{project_id}/approvals/{approval_id}")

    def close(self, project_id: str, approval_id: str, status: str):
        return self.client.put(
            f"projects/{project_id}/approvals/{approval_id}/close",
            params={"status": status},
        )


class BOMsAPI(_BaseAPI):
    def list(self, project_id: str, branch_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/boms")

    def get(self, project_id: str, branch_id: str, bom_id: str):
        return self.client.get(f"projects/{project_id}/branches/{branch_id}/boms/{bom_id}")

    def download(self, project_id: str, branch_id: str, bom_id: str, payload: dict):
        return self.client.post(
            f"projects/{project_id}/branches/{branch_id}/boms/{bom_id}/download",
            json=payload,
        )


class SearchAPI(_BaseAPI):
    def files(
        self,
        search_key: str,
        *,
        page_size: int | None = None,
        from_offset: int | None = None,
    ):
        return self.client.put(
            "search",
            json={"search_key": search_key},
            params=_omit_none({"pageSize": page_size, "from": from_offset}) or None,
        )


class WebhooksAPI(_BaseAPI):
    def list(self):
        return self.client.get("webhooks/subscriptions")

    def create(self, payload: dict):
        return self.client.post("webhooks/subscriptions", json=payload)

    def get(self, subscription_id: str):
        return self.client.get(f"webhooks/subscriptions/{subscription_id}")

    def update(self, subscription_id: str, payload: dict):
        return self.client.put(f"webhooks/subscriptions/{subscription_id}", json=payload)

    def delete(self, subscription_id: str):
        return self.client.delete(f"webhooks/subscriptions/{subscription_id}")

    def rotate_secret(self, subscription_id: str):
        return self.client.post(f"webhooks/subscriptions/{subscription_id}/rotate")


def _omit_none(data: dict) -> dict:
    return {key: value for key, value in data.items() if value is not None}


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
