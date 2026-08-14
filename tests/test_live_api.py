from __future__ import annotations

import os
import unittest
from typing import Any

from bild import BildAPIError, BildClient


def _as_list(payload: Any, *keys: str) -> list:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    preferred = keys or (
        "data",
        "items",
        "commits",
        "files",
        "sharedLinks",
        "packages",
        "revisions",
        "approvals",
        "boms",
        "feedbackItems",
    )
    for key in preferred:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _as_list(value, *keys)
            if nested:
                return nested

    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return _as_list(data, *keys)
    return []


def _first_id(items: list, *keys: str) -> str | None:
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys or ("id",):
            value = item.get(key)
            if value:
                return str(value)
    return None


@unittest.skipUnless(os.getenv("BILD_API_KEY"), "BILD_API_KEY not set")
class TestLiveAPI(unittest.TestCase):
    """Hit the real Bild API with read-only calls. Write/delete endpoints are skipped."""

    client: BildClient
    project_id: str
    branch_id: str
    file_id: str | None
    version_id: str | None
    commit_id: str | None

    @classmethod
    def setUpClass(cls):
        cls.client = BildClient(timeout=60.0)
        projects = _as_list(cls.client.api.projects.list())
        if not projects:
            raise unittest.SkipTest("No projects available for live tests")

        project = next((p for p in projects if p.get("name") == "Sandboxes"), projects[0])
        cls.project_id = project["id"]
        cls.branch_id = cls.client.resolve_branch_id(cls.project_id)
        cls.file_id = None
        cls.version_id = None
        cls.commit_id = None

        commits = _as_list(cls.client.api.commits.list(cls.project_id, cls.branch_id), "commits")
        cls.commit_id = _first_id(commits, "id")
        if cls.commit_id:
            detail = cls.client.api.commits.get(cls.project_id, cls.branch_id, cls.commit_id)
            files = []
            if isinstance(detail, dict):
                data = detail.get("data") if isinstance(detail.get("data"), dict) else detail
                files = data.get("files") or []
            cls.file_id = _first_id(files, "fileID", "fileId")
            cls.version_id = _first_id(files, "fileVersionID", "versionID", "id")

        if not cls.file_id:
            released = _as_list(cls.client.api.files.list_released("2026-01-01T00:00:00Z"))
            match = next(
                (
                    item
                    for item in released
                    if isinstance(item, dict) and item.get("projectID") == cls.project_id
                ),
                None,
            )
            if match:
                cls.file_id = match.get("fileID") or match.get("id")
                cls.version_id = match.get("versionID") or match.get("fileVersionID")

        if cls.file_id and not cls.version_id:
            latest = cls.client.api.files.get_latest(cls.project_id, cls.branch_id, cls.file_id)
            if isinstance(latest, dict):
                data = latest.get("data") if isinstance(latest.get("data"), dict) else latest
                cls.version_id = (
                    data.get("fileVersionID") or data.get("fileVersion") or data.get("versionId")
                )

    def test_list_users(self):
        users = _as_list(self.client.api.users.list())
        self.assertGreater(len(users), 0)
        self.assertTrue(users[0].get("id") or users[0].get("email"))

    def test_list_projects(self):
        projects = _as_list(self.client.api.projects.list())
        self.assertGreater(len(projects), 0)
        self.assertTrue(any(p.get("id") == self.project_id for p in projects))

    def test_list_project_users(self):
        users = _as_list(self.client.api.project_users.list(self.project_id))
        self.assertGreater(len(users), 0)

    def test_list_branches(self):
        branches = _as_list(self.client.api.branches.list(self.project_id))
        self.assertGreater(len(branches), 0)
        self.assertTrue(any((b.get("id") or b.get("branchId")) == self.branch_id for b in branches))

    def test_list_commits(self):
        commits = _as_list(self.client.api.commits.list(self.project_id, self.branch_id), "commits")
        self.assertIsInstance(commits, list)

    def test_get_commit(self):
        if not self.commit_id:
            self.skipTest("No commits available")
        detail = self.client.api.commits.get(self.project_id, self.branch_id, self.commit_id)
        self.assertIsInstance(detail, dict)
        data = detail.get("data") if isinstance(detail.get("data"), dict) else detail
        self.assertEqual(data.get("id"), self.commit_id)

    def test_list_files(self):
        payload = self.client.api.files.list(self.project_id, self.branch_id)
        self.assertIsInstance(payload, dict)
        self.assertTrue(
            isinstance(payload.get("data"), (list, dict))
            or payload.get("s3Url")
            or payload.get("items")
        )

    def test_list_released_files(self):
        payload = self.client.api.files.list_released("2026-01-01T00:00:00Z")
        self.assertIsInstance(payload, (dict, list))
        files = _as_list(payload)
        self.assertIsInstance(files, list)

    def test_file_versions_and_latest(self):
        if not self.file_id:
            self.skipTest("No file available")
        versions = _as_list(
            self.client.api.files.list_versions(self.project_id, self.branch_id, self.file_id)
        )
        self.assertGreater(len(versions), 0)
        latest = self.client.api.files.get_latest(self.project_id, self.branch_id, self.file_id)
        self.assertIsInstance(latest, dict)
        data = latest.get("data") if isinstance(latest.get("data"), dict) else latest
        self.assertTrue(data.get("fileVersionID") or data.get("fileID"))

    def test_file_version_detail(self):
        if not self.file_id or not self.version_id:
            self.skipTest("No file version available")
        detail = self.client.api.files.get_version(
            self.project_id, self.branch_id, self.file_id, self.version_id
        )
        self.assertIsInstance(detail, dict)

    def test_file_thumbnail(self):
        if not self.file_id or not self.version_id:
            self.skipTest("No file version available")
        payload = self.client.api.files.get_thumbnail(
            self.project_id, self.branch_id, self.file_id, self.version_id
        )
        self.assertIsInstance(payload, dict)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        self.assertTrue(data.get("thumbnailURL") or data.get("url") or payload)

    def test_file_children(self):
        if not self.file_id or not self.version_id:
            self.skipTest("No file version available")
        payload = self.client.api.files.get_children(
            self.project_id, self.branch_id, self.file_id, self.version_id
        )
        self.assertIsInstance(payload, (dict, list))

    def test_shared_links(self):
        account = self.client.api.shared_links.list()
        project = self.client.api.shared_links.list(self.project_id)
        branch = self.client.api.shared_links.list(self.project_id, self.branch_id)
        self.assertIsInstance(account, dict)
        self.assertIsInstance(project, dict)
        self.assertIsInstance(branch, dict)

    def test_metadata_fields(self):
        fields = _as_list(self.client.api.metadata.list_fields())
        self.assertGreater(len(fields), 0)
        self.assertTrue(fields[0].get("id") or fields[0].get("name"))

    def test_file_metadata(self):
        if not self.file_id:
            self.skipTest("No file available")
        payload = self.client.api.metadata.get(self.project_id, self.branch_id, self.file_id)
        self.assertIsInstance(payload, dict)
        if self.version_id:
            versioned = self.client.api.metadata.get_for_version(
                self.project_id, self.branch_id, self.file_id, self.version_id
            )
            self.assertIsInstance(versioned, dict)

    def test_feedback(self):
        payload = self.client.api.feedback.list(self.project_id)
        self.assertIsInstance(payload, dict)
        items = _as_list(payload, "feedbackItems")
        self.assertIsInstance(items, list)
        if items:
            item_id = _first_id(items, "id")
            detail = self.client.api.feedback.get(self.project_id, item_id)
            self.assertIsInstance(detail, dict)

    def test_packages(self):
        account = self.client.api.packages.list()
        project = self.client.api.packages.list(self.project_id)
        self.assertIsInstance(account, dict)
        self.assertIsInstance(project, dict)
        packages = _as_list(account, "packages")
        if packages:
            package_id = _first_id(packages, "id")
            package_project = packages[0].get("projectID") or self.project_id
            detail = self.client.api.packages.get(package_project, package_id)
            self.assertIsInstance(detail, dict)

    def test_revisions(self):
        account = self.client.api.revisions.list()
        project = self.client.api.revisions.list(self.project_id)
        branch = self.client.api.revisions.list(self.project_id, self.branch_id)
        self.assertIsInstance(account, (dict, list))
        self.assertIsInstance(project, (dict, list))
        self.assertIsInstance(branch, (dict, list))
        if self.file_id:
            file_revs = self.client.api.revisions.list(
                self.project_id, self.branch_id, self.file_id
            )
            revisions = _as_list(file_revs, "revisions")
            self.assertIsInstance(revisions, list)
            revision_id = _first_id(revisions, "id")
            if revision_id:
                detail = self.client.api.revisions.get(
                    self.project_id, self.branch_id, self.file_id, revision_id
                )
                self.assertIsInstance(detail, dict)
            closure = self.client.api.revisions.get_closure(
                self.project_id, self.branch_id, self.file_id
            )
            self.assertIsInstance(closure, dict)

    def test_approvals(self):
        account = self.client.api.approvals.list()
        project = self.client.api.approvals.list(self.project_id)
        self.assertIsInstance(account, dict)
        self.assertIsInstance(project, dict)

    def test_boms(self):
        payload = self.client.api.boms.list(self.project_id, self.branch_id)
        self.assertIsInstance(payload, dict)
        boms = _as_list(payload, "boms")
        if boms:
            bom_id = _first_id(boms, "id")
            detail = self.client.api.boms.get(self.project_id, self.branch_id, bom_id)
            self.assertIsInstance(detail, dict)

    def test_search_files(self):
        payload = self.client.api.search.files("bolt", page_size=5)
        self.assertIsInstance(payload, dict)
        files = _as_list(payload, "files")
        self.assertGreater(len(files), 0)

    def test_webhooks(self):
        payload = self.client.api.webhooks.list()
        self.assertIsInstance(payload, (dict, list))

    def test_released_file_is_optional(self):
        if not self.file_id:
            self.skipTest("No file available")
        try:
            payload = self.client.api.files.get_released(
                self.project_id, self.branch_id, self.file_id
            )
        except BildAPIError as exc:
            self.assertEqual(exc.status_code, 404)
            return
        self.assertIsInstance(payload, dict)


if __name__ == "__main__":
    unittest.main()
