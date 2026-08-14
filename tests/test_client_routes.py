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
        if path.endswith("/latest"):
            return FakeResponse(200, {"data": {"fileVersion": "v-latest"}})

        return FakeResponse(200, {"ok": True, "path": path})


class TestBildClientRoutes(unittest.TestCase):
    def setUp(self):
        self.client = BildClient(token="test-token", session=FakeSession())

    def last(self):
        return self.client.session.calls[-1]

    def test_full_route_coverage(self):
        c = self.client

        c.api.users.list()
        self.assertTrue(self.last()["path"].endswith("/users"))
        c.api.users.invite(["a@example.com"], projects=[{"id": "p1"}])
        self.assertTrue(self.last()["path"].endswith("/users/add"))
        self.assertEqual(self.last()["method"], "PUT")
        c.api.users.remove(["u1"])
        self.assertTrue(self.last()["path"].endswith("/users/remove"))
        c.api.users.update(["u1"], projects=[])
        self.assertTrue(self.last()["path"].endswith("/users/update"))
        c.api.users.create_token(name="ci")
        self.assertTrue(self.last()["path"].endswith("/users/apiToken"))
        self.assertEqual(self.last()["method"], "POST")

        c.api.projects.list()
        self.assertTrue(self.last()["path"].endswith("/projects"))

        c.api.project_users.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/users"))
        c.api.project_users.add([{"id": "u1", "accessType": "Editor"}], project_ids=["p1"])
        self.assertTrue(self.last()["path"].endswith("/projects/users/add"))
        self.assertEqual(self.last()["method"], "POST")
        c.api.project_users.update([{"id": "u1", "accessType": "Viewer"}], project_ids=["p1"])
        self.assertTrue(self.last()["path"].endswith("/projects/users/update"))
        c.api.project_users.remove(["p1"], ["u1"])
        self.assertTrue(self.last()["path"].endswith("/projects/users/remove"))

        c.api.branches.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches"))

        c.api.commits.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/commits"))
        c.api.commits.list("p1", "b1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/commits"))
        c.api.commits.get("p1", "b1", "c1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/commits/c1"))

        c.api.files.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/files"))
        c.api.files.list("p1", "b1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/files"))
        c.api.files.list_released("2024-01-01T00:00:00Z")
        self.assertTrue(self.last()["path"].endswith("/files/released"))
        self.assertEqual(self.last()["params"]["fromTime"], "2024-01-01T00:00:00Z")
        c.api.files.list_versions("p1", None, "f1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/branch-main/files/f1/versions"))
        c.api.files.get_latest("p1", None, "f1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/branch-main/files/f1/latest"))
        c.api.files.get_released("p1", "b1", "f1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/files/f1/released"))
        c.api.files.get_version("p1", "b1", "f1", "v1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/files/f1/versions/v1"))
        c.api.files.get_thumbnail("p1", "b1", "f1", "v1")
        self.assertTrue(self.last()["path"].endswith("/thumbnail"))
        c.api.files.get_children("p1", "b1", "f1", "v1")
        self.assertTrue(self.last()["path"].endswith("/children"))
        c.api.files.export_universal("p1", None, "f1", output_format="stl")
        self.assertTrue(self.last()["path"].endswith("/fileActions/f1/universalFormat"))
        self.assertEqual(self.last()["method"], "PUT")
        self.assertEqual(self.last()["json"]["fileVersionID"], "v-latest")
        c.api.files.export_universal_many("p1", "b1", {"fileIDs": ["f1"], "formats": {"CAD": ["STL"]}})
        self.assertTrue(self.last()["path"].endswith("/files/exportUniversalFiles"))
        c.api.files.move("p1", "b1", ["f1"], "parent-1")
        self.assertTrue(self.last()["path"].endswith("/fileActions/move"))
        c.api.files.delete("p1", "b1", ["f1"])
        self.assertTrue(self.last()["path"].endswith("/fileActions/delete"))

        c.api.uploads.initiate("p1", "b1", [{"name": "x"}])
        self.assertTrue(self.last()["path"].endswith("/fileActions/initiateUpload"))
        c.api.uploads.complete("p1", "b1", [{"id": "x"}])
        self.assertTrue(self.last()["path"].endswith("/fileActions/completeUpload"))
        self.assertEqual(self.last()["method"], "POST")

        c.api.checkouts.checkout("p1", "b1", ["f1"])
        self.assertTrue(self.last()["path"].endswith("/fileActions/checkout"))
        c.api.checkouts.cancel("p1", "b1", ["f1"])
        self.assertTrue(self.last()["path"].endswith("/fileActions/cancelCheckout"))
        c.api.checkouts.initiate_checkin("p1", "b1", [{"id": "f1"}])
        self.assertTrue(self.last()["path"].endswith("/fileActions/initiateCheckin"))
        c.api.checkouts.complete_checkin("p1", "b1", [{"id": "f1"}], message="v2")
        self.assertTrue(self.last()["path"].endswith("/fileActions/completeCheckin"))

        c.api.shared_links.list()
        self.assertTrue(self.last()["path"].endswith("/sharedLinks"))
        c.api.shared_links.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/sharedLinks"))
        c.api.shared_links.list("p1", "b1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/sharedLinks"))
        c.api.shared_links.create_live("p1", "b1", "Review Link", ["f1"])
        self.assertTrue(self.last()["path"].endswith("/files/sharedLink"))
        self.assertEqual(self.last()["method"], "POST")
        c.api.shared_links.create_static("p1", "b1", "f1", "v1")
        self.assertTrue(self.last()["path"].endswith("/fileVersion/v1/sharedLink"))
        c.api.shared_links.refresh("p1", "b1", "s1")
        self.assertTrue(self.last()["path"].endswith("/sharedLinks/s1/refresh"))
        c.api.shared_links.delete("p1", "b1", ["s1"])
        self.assertTrue(self.last()["path"].endswith("/sharedLinks/delete"))

        c.api.metadata.list_fields()
        self.assertTrue(self.last()["path"].endswith("/metadataFields"))
        c.api.metadata.get("p1", "b1", "f1")
        self.assertTrue(self.last()["path"].endswith("/files/f1/metadata"))
        c.api.metadata.get_for_version("p1", "b1", "f1", "v1")
        self.assertTrue(self.last()["path"].endswith("/versions/v1/metadata"))
        c.api.metadata.update("p1", "b1", {"fileIDs": ["f1"]})
        self.assertTrue(self.last()["path"].endswith("/files/updateMetadata"))

        c.api.feedback.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/feedbackItems"))
        c.api.feedback.list("p1", file_id="f1")
        self.assertTrue(self.last()["path"].endswith("/files/f1/feedbackItems"))
        c.api.feedback.get("p1", "i1")
        self.assertTrue(self.last()["path"].endswith("/feedbackItems/i1"))
        c.api.feedback.update("p1", "i1", {"status": "inProgress"})
        self.assertEqual(self.last()["method"], "PUT")
        c.api.feedback.initiate_attachment("p1", "i1", {"fileName": "a.txt"})
        self.assertTrue(self.last()["path"].endswith("/feedbackItems/i1/attachment"))
        c.api.feedback.complete_attachment("p1", "i1", "att1", {"name": "a.txt"})
        self.assertTrue(self.last()["path"].endswith("/attachment/att1"))
        self.assertEqual(self.last()["method"], "POST")
        c.api.feedback.delete_attachment("p1", "i1", "att1")
        self.assertEqual(self.last()["method"], "DELETE")

        c.api.packages.list()
        self.assertTrue(self.last()["path"].endswith("/packages"))
        c.api.packages.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/packages"))
        c.api.packages.get("p1", "pkg1")
        self.assertTrue(self.last()["path"].endswith("/packages/pkg1"))

        c.api.revisions.list()
        self.assertTrue(self.last()["path"].endswith("/revisions"))
        c.api.revisions.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/revisions"))
        c.api.revisions.list("p1", "b1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/revisions"))
        c.api.revisions.list("p1", "b1", "f1")
        self.assertTrue(self.last()["path"].endswith("/files/f1/revisions"))
        c.api.revisions.get("p1", "b1", "f1", "r1")
        self.assertTrue(self.last()["path"].endswith("/revisions/r1"))
        c.api.revisions.get_closure("p1", "b1", "f1")
        self.assertTrue(self.last()["path"].endswith("/files/f1/closure"))
        c.api.revisions.release("p1", "b1", [{"revisionID": "r1", "revisionNumber": "A"}])
        self.assertTrue(self.last()["path"].endswith("/revisions/release"))
        c.api.revisions.cancel("p1", "b1", ["r1"])
        self.assertTrue(self.last()["path"].endswith("/revisions/cancel"))

        c.api.approvals.list()
        self.assertTrue(self.last()["path"].endswith("/approvals"))
        c.api.approvals.list("p1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/approvals"))
        c.api.approvals.get("p1", "a1")
        self.assertTrue(self.last()["path"].endswith("/approvals/a1"))
        c.api.approvals.close("p1", "a1", "approved")
        self.assertTrue(self.last()["path"].endswith("/approvals/a1/close"))
        self.assertEqual(self.last()["params"]["status"], "approved")

        c.api.boms.list("p1", "b1")
        self.assertTrue(self.last()["path"].endswith("/projects/p1/branches/b1/boms"))
        c.api.boms.get("p1", "b1", "bom1")
        self.assertTrue(self.last()["path"].endswith("/boms/bom1"))
        c.api.boms.download("p1", "b1", "bom1", {"version_id": "v", "view_id": "w", "type": "Indented", "formats": {}})
        self.assertTrue(self.last()["path"].endswith("/boms/bom1/download"))

        c.api.search.files("bolt")
        self.assertEqual(self.last()["method"], "PUT")
        self.assertTrue(self.last()["path"].endswith("/search"))
        self.assertEqual(self.last()["json"]["search_key"], "bolt")

        c.api.webhooks.list()
        self.assertTrue(self.last()["path"].endswith("/webhooks/subscriptions"))
        c.api.webhooks.create({"eventType": "file.updated", "targetURL": "https://example.com"})
        self.assertEqual(self.last()["method"], "POST")
        c.api.webhooks.get("sub1")
        self.assertTrue(self.last()["path"].endswith("/webhooks/subscriptions/sub1"))
        c.api.webhooks.update("sub1", {"isActive": False})
        self.assertEqual(self.last()["method"], "PUT")
        c.api.webhooks.rotate_secret("sub1")
        self.assertTrue(self.last()["path"].endswith("/rotate"))
        c.api.webhooks.delete("sub1")
        self.assertEqual(self.last()["method"], "DELETE")


if __name__ == "__main__":
    unittest.main()
