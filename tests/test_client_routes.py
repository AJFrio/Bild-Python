from __future__ import annotations

import unittest
from dataclasses import dataclass
from urllib.parse import urlparse
import sys
import types

if "requests" not in sys.modules:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildClient


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


class FakeSession:
    def __init__(self):
        self.calls = []
        self.headers = {}

    def request(self, method, url, params=None, json=None, timeout=None):
        path = urlparse(url).path
        self.calls.append({"method": method.upper(), "path": path, "json": json, "params": params})

        if path.endswith("/branches"):
            return FakeResponse(200, {"data": [{"id": "branch-main", "isMain": True}]})
        if path.endswith("/latestFileVersion"):
            return FakeResponse(200, {"data": {"fileVersion": "v-latest"}})

        return FakeResponse(200, {"ok": True, "path": path})


class TestBildClientRoutes(unittest.TestCase):
    def setUp(self):
        self.client = BildClient(token="test-token", session=FakeSession())

    def last(self):
        return self.client.session.calls[-1]

    def test_full_route_coverage(self):
        c = self.client

        c.api.users.list(); self.assertTrue(self.last()["path"].endswith("/api/users"))
        c.api.users.add(["a@example.com"]); self.assertTrue(self.last()["path"].endswith("/api/users/add"))

        c.api.projects.list(); self.assertTrue(self.last()["path"].endswith("/api/projects"))

        c.api.project_users.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/users"))
        c.api.project_users.add("p1", {"userId": "u1"}); self.assertEqual(self.last()["method"], "POST")
        c.api.project_users.update("p1", "u1", {"role": "Editor"}); self.assertEqual(self.last()["method"], "PUT")

        c.api.branches_commits.list_branches("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches"))
        c.api.branches_commits.branch("p1", "b1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1"))
        c.api.branches_commits.commits("p1", "b1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/commits"))
        c.api.branches_commits.commit("p1", "b1", "c1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/commits/c1"))

        c.api.files.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/files"))
        c.api.files.list("p1", "b1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files"))
        c.api.files.get("p1", None, "f1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/branch-main/files/f1"))
        c.api.files.latest_version("p1", None, "f1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/branch-main/files/f1/latestFileVersion"))
        c.api.files.universal_format("p1", None, "f1", file_version=None, output_format="stl")
        self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/branch-main/files/f1/universalFormat"))
        self.assertEqual(self.last()["json"]["fileVersion"], "v-latest")

        c.api.file_upload.init_upload("p1", "b1", {"name": "x"}); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/fileUpload"))
        c.api.file_upload.complete_upload("p1", "b1", {"id": "x"}); self.assertEqual(self.last()["method"], "POST")

        c.api.file_checkin_checkout.checkout("p1", "b1", "f1"); self.assertTrue(self.last()["path"].endswith("/checkout"))
        c.api.file_checkin_checkout.checkin("p1", "b1", "f1"); self.assertTrue(self.last()["path"].endswith("/checkin"))
        c.api.file_checkin_checkout.discard_checkout("p1", "b1", "f1"); self.assertTrue(self.last()["path"].endswith("/discardCheckout"))
        c.api.file_checkin_checkout.create_version("p1", "b1", "f1", {"message": "v2"}); self.assertTrue(self.last()["path"].endswith("/versions"))

        c.api.shared_links.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/sharedLinks"))
        c.api.shared_links.get("p1", "s1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/sharedLinks/s1"))
        c.api.shared_links.create("p1", {"x": 1}); self.assertEqual(self.last()["method"], "POST")
        c.api.shared_links.update("p1", "s1", {"x": 2}); self.assertEqual(self.last()["method"], "PUT")

        c.api.files_move_delete.move("p1", "b1", {"ids": ["f1"]}); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files/move"))
        c.api.files_move_delete.delete_many("p1", "b1", {"ids": ["f1"]}); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files/delete"))

        c.api.files_metadata.fields(); self.assertTrue(self.last()["path"].endswith("/api/metadataFields"))
        c.api.files_metadata.file_metadata("p1", "b1", "f1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files/f1/metadata"))
        c.api.files_metadata.update_file_metadata("p1", "b1", "f1", {"a": 1}); self.assertEqual(self.last()["method"], "PUT")

        c.api.feedback_items.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/feedbackItems"))
        c.api.feedback_items.get("p1", "i1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/feedbackItems/i1"))
        c.api.feedback_items.create("p1", {"x": 1}); self.assertEqual(self.last()["method"], "POST")
        c.api.feedback_items.update("p1", "i1", {"x": 2}); self.assertEqual(self.last()["method"], "PUT")
        c.api.feedback_items.delete("p1", "i1"); self.assertEqual(self.last()["method"], "DELETE")

        c.api.packages.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/packages"))
        c.api.packages.get("p1", "pkg1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/packages/pkg1"))

        c.api.revisions.list("p1", "b1", "f1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files/f1/revisions"))
        c.api.revisions.get("p1", "b1", "f1", "r1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/branches/b1/files/f1/revisions/r1"))
        c.api.revisions.restore("p1", "b1", "f1", "r1"); self.assertTrue(self.last()["path"].endswith("/restore"))

        c.api.approvals.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/approvals"))
        c.api.approvals.get("p1", "a1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/approvals/a1"))
        c.api.approvals.update("p1", "a1", {"status": "approved"}); self.assertEqual(self.last()["method"], "PUT")

        c.api.boms.list("p1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/boms"))
        c.api.boms.get("p1", "bom1"); self.assertTrue(self.last()["path"].endswith("/api/projects/p1/boms/bom1"))
        c.api.boms.create("p1", {"x": 1}); self.assertEqual(self.last()["method"], "POST")

        c.api.search.query({"query": "bolt"}); self.assertEqual(self.last()["method"], "PUT")
        self.assertTrue(self.last()["path"].endswith("/api/search"))


if __name__ == "__main__":
    unittest.main()
