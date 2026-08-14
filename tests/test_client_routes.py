from __future__ import annotations

import inspect
import sys
import types
import unittest
from pathlib import Path

try:
    import requests  # noqa: F401
except ImportError:
    fake_requests = types.ModuleType("requests")
    fake_requests.Session = object
    fake_requests.Response = object
    sys.modules["requests"] = fake_requests

from bild import BildClient
from bild.client import _Resources
from tests.fakes import RouteSession


class TestBildClientRoutes(unittest.TestCase):
    def setUp(self):
        self.client = BildClient(token="test-token", session=RouteSession())

    def last(self):
        return self.client.session.calls[-1]

    def assert_call(self, method: str, path_suffix: str, *, json=None, params=None):
        call = self.last()
        self.assertEqual(call["method"], method, call)
        self.assertTrue(
            call["path"].endswith(path_suffix),
            f"expected path ending {path_suffix!r}, got {call['path']!r}",
        )
        if method in ("GET", "DELETE"):
            self.assertIsNone(call["json"], call)
        if json is not None:
            self.assertEqual(call["json"], json)
        if params is not None:
            self.assertEqual(call["params"], params)

    def test_verify(self):
        verified = self.client.verify()
        self.assertEqual(verified["function"], "BildClient.verify")
        self.assertTrue(verified["ok"])
        self.assert_call("GET", "/projects")

    def test_users(self):
        c = self.client
        c.api.users.list()
        self.assert_call("GET", "/users")

        c.api.users.invite(
            ["a@example.com"],
            projects=[{"id": "p1"}],
            pdm_role="Member",
        )
        self.assert_call(
            "PUT",
            "/users/add",
            json={
                "emails": ["a@example.com"],
                "projects": [{"id": "p1"}],
                "pdmRole": "Member",
            },
        )

        c.api.users.remove(["u1"])
        self.assert_call("PUT", "/users/remove", json={"userIDs": ["u1"]})

        c.api.users.update(["u1"], projects=[], company_role="Admin")
        self.assert_call(
            "PUT",
            "/users/update",
            json={"userIDs": ["u1"], "projects": [], "companyRole": "Admin"},
        )

        c.api.users.create_token(name="ci")
        self.assert_call("POST", "/users/apiToken", json={"name": "ci"})

    def test_projects(self):
        self.client.api.projects.list()
        self.assert_call("GET", "/projects")

    def test_project_users(self):
        c = self.client
        c.api.project_users.list("p1")
        self.assert_call("GET", "/projects/p1/users")

        c.api.project_users.add([{"id": "u1", "accessType": "Editor"}], project_ids=["p1"])
        self.assert_call(
            "POST",
            "/projects/users/add",
            json={"users": [{"id": "u1", "accessType": "Editor"}], "projectIDs": ["p1"]},
        )

        c.api.project_users.update([{"id": "u1", "accessType": "Viewer"}], project_ids=["p1"])
        self.assert_call(
            "PUT",
            "/projects/users/update",
            json={"users": [{"id": "u1", "accessType": "Viewer"}], "projectIDs": ["p1"]},
        )

        c.api.project_users.remove(["p1"], ["u1"])
        self.assert_call(
            "PUT",
            "/projects/users/remove",
            json={"projectIDs": ["p1"], "userIDs": ["u1"]},
        )

    def test_branches(self):
        self.client.api.branches.list("p1")
        self.assert_call("GET", "/projects/p1/branches")

    def test_commits(self):
        c = self.client
        c.api.commits.list("p1")
        self.assert_call("GET", "/projects/p1/commits")
        c.api.commits.list("p1", "b1")
        self.assert_call("GET", "/projects/p1/branches/b1/commits")
        c.api.commits.get("p1", "b1", "c1")
        self.assert_call("GET", "/projects/p1/branches/b1/commits/c1")

    def test_files(self):
        c = self.client
        c.api.files.list("p1")
        self.assert_call("GET", "/projects/p1/files")
        c.api.files.list("p1", "b1")
        self.assert_call("GET", "/projects/p1/branches/b1/files")

        c.api.files.list_released("2024-01-01T00:00:00Z")
        self.assert_call("GET", "/files/released", params={"fromTime": "2024-01-01T00:00:00Z"})

        c.api.files.list_versions("p1", None, "f1")
        self.assert_call("GET", "/projects/p1/branches/branch-main/files/f1/versions")
        c.api.files.get_latest("p1", None, "f1")
        self.assert_call("GET", "/projects/p1/branches/branch-main/files/f1/latest")
        c.api.files.get_released("p1", "b1", "f1")
        self.assert_call("GET", "/projects/p1/branches/b1/files/f1/released")
        c.api.files.get_version("p1", "b1", "f1", "v1")
        self.assert_call("GET", "/projects/p1/branches/b1/files/f1/versions/v1")
        c.api.files.get_thumbnail("p1", "b1", "f1", "v1")
        self.assert_call("GET", "/thumbnail")
        c.api.files.get_children("p1", "b1", "f1", "v1")
        self.assert_call("GET", "/children")

        c.api.files.export_universal("p1", None, "f1", output_format="stl")
        self.assert_call(
            "PUT",
            "/fileActions/f1/universalFormat",
            json={"fileVersionID": "v-latest", "universalFileFormat": "stl"},
        )
        c.api.files.export_universal(
            "p1", "b1", "f1", output_format="step", file_version="v1", file_config="cfg"
        )
        self.assert_call(
            "PUT",
            "/fileActions/f1/universalFormat",
            json={
                "fileVersionID": "v1",
                "universalFileFormat": "step",
                "fileConfig": "cfg",
            },
        )

        c.api.files.export_universal_many(
            "p1", "b1", {"fileIDs": ["f1"], "formats": {"CAD": ["STL"]}}
        )
        self.assert_call(
            "POST",
            "/files/exportUniversalFiles",
            json={"fileIDs": ["f1"], "formats": {"CAD": ["STL"]}},
        )

        c.api.files.move("p1", "b1", ["f1"], "parent-1")
        self.assert_call(
            "PUT",
            "/fileActions/move",
            json={"moveFiles": ["f1"], "newParentID": "parent-1"},
        )
        c.api.files.delete("p1", "b1", ["f1"])
        self.assert_call("PUT", "/fileActions/delete", json={"fileIDs": ["f1"]})

    def test_uploads(self):
        c = self.client
        c.api.uploads.initiate("p1", "b1", [{"name": "x"}])
        self.assert_call("PUT", "/fileActions/initiateUpload", json={"files": [{"name": "x"}]})
        c.api.uploads.complete("p1", "b1", [{"id": "x"}])
        self.assert_call("POST", "/fileActions/completeUpload", json={"files": [{"id": "x"}]})
        c.api.uploads.complete("p1", "b1", [{"id": "x"}], keep_checked_out=True)
        self.assert_call(
            "POST",
            "/fileActions/completeUpload",
            json={"files": [{"id": "x"}], "keepFilesCheckedOut": True},
        )

    def test_checkouts(self):
        c = self.client
        c.api.checkouts.checkout("p1", "b1", ["f1"])
        self.assert_call("PUT", "/fileActions/checkout", json={"fileIDs": ["f1"]})
        c.api.checkouts.cancel("p1", "b1", ["f1"])
        self.assert_call("PUT", "/fileActions/cancelCheckout", json={"fileIDs": ["f1"]})
        c.api.checkouts.initiate_checkin("p1", "b1", [{"id": "f1"}])
        self.assert_call("PUT", "/fileActions/initiateCheckin", json={"files": [{"id": "f1"}]})
        c.api.checkouts.complete_checkin("p1", "b1", [{"id": "f1"}], message="v2")
        self.assert_call(
            "POST",
            "/fileActions/completeCheckin",
            json={"files": [{"id": "f1"}], "message": "v2"},
        )

    def test_shared_links(self):
        c = self.client
        c.api.shared_links.list()
        self.assert_call("GET", "/sharedLinks")
        c.api.shared_links.list("p1")
        self.assert_call("GET", "/projects/p1/sharedLinks")
        c.api.shared_links.list("p1", "b1")
        self.assert_call("GET", "/projects/p1/branches/b1/sharedLinks")

        c.api.shared_links.create_live("p1", "b1", "Review Link", ["f1"])
        self.assert_call(
            "POST",
            "/files/sharedLink",
            json={"name": "Review Link", "fileIDs": ["f1"]},
        )
        c.api.shared_links.create_live(
            "p1",
            "b1",
            "Review Link",
            ["f1"],
            types=["stl"],
            config_map={"f1": "cfg"},
        )
        self.assert_call(
            "POST",
            "/files/sharedLink",
            json={
                "name": "Review Link",
                "fileIDs": ["f1"],
                "types": ["stl"],
                "configMap": {"f1": "cfg"},
            },
        )

        c.api.shared_links.create_static("p1", "b1", "f1", "v1")
        self.assert_call("POST", "/fileVersion/v1/sharedLink", json={})
        c.api.shared_links.refresh("p1", "b1", "s1")
        self.assert_call("PUT", "/sharedLinks/s1/refresh")
        self.assertIsNone(self.last()["json"])
        c.api.shared_links.delete("p1", "b1", ["s1"])
        self.assert_call("PUT", "/sharedLinks/delete", json={"sharedLinkIDs": ["s1"]})

    def test_metadata(self):
        c = self.client
        c.api.metadata.list_fields()
        self.assert_call("GET", "/metadataFields")
        c.api.metadata.get("p1", "b1", "f1")
        self.assert_call("GET", "/files/f1/metadata")
        c.api.metadata.get_for_version("p1", "b1", "f1", "v1")
        self.assert_call("GET", "/versions/v1/metadata")
        c.api.metadata.update("p1", "b1", {"fileIDs": ["f1"]})
        self.assert_call("PUT", "/files/updateMetadata", json={"fileIDs": ["f1"]})

    def test_feedback(self):
        c = self.client
        c.api.feedback.list("p1")
        self.assert_call("GET", "/projects/p1/feedbackItems")
        c.api.feedback.list("p1", file_id="f1")
        self.assert_call("GET", "/files/f1/feedbackItems")
        c.api.feedback.get("p1", "i1")
        self.assert_call("GET", "/feedbackItems/i1")
        c.api.feedback.update("p1", "i1", {"status": "inProgress"})
        self.assert_call("PUT", "/feedbackItems/i1", json={"status": "inProgress"})
        c.api.feedback.initiate_attachment("p1", "i1", {"fileName": "a.txt"})
        self.assert_call("PUT", "/feedbackItems/i1/attachment", json={"fileName": "a.txt"})
        c.api.feedback.complete_attachment("p1", "i1", "att1", {"name": "a.txt"})
        self.assert_call("POST", "/attachment/att1", json={"name": "a.txt"})
        c.api.feedback.delete_attachment("p1", "i1", "att1")
        self.assert_call("DELETE", "/attachment/att1")

    def test_packages(self):
        c = self.client
        c.api.packages.list()
        self.assert_call("GET", "/packages")
        c.api.packages.list("p1")
        self.assert_call("GET", "/projects/p1/packages")
        c.api.packages.get("p1", "pkg1")
        self.assert_call("GET", "/packages/pkg1")

    def test_revisions(self):
        c = self.client
        c.api.revisions.list()
        self.assert_call("GET", "/revisions")
        c.api.revisions.list("p1")
        self.assert_call("GET", "/projects/p1/revisions")
        c.api.revisions.list("p1", "b1")
        self.assert_call("GET", "/projects/p1/branches/b1/revisions")
        c.api.revisions.list("p1", "b1", "f1")
        self.assert_call("GET", "/files/f1/revisions")
        c.api.revisions.get("p1", "b1", "f1", "r1")
        self.assert_call("GET", "/revisions/r1")
        c.api.revisions.get_closure("p1", "b1", "f1")
        self.assert_call("GET", "/files/f1/closure")
        c.api.revisions.release("p1", "b1", [{"revisionID": "r1", "revisionNumber": "A"}])
        self.assert_call(
            "PUT",
            "/revisions/release",
            json=[{"revisionID": "r1", "revisionNumber": "A"}],
        )
        c.api.revisions.cancel("p1", "b1", ["r1"])
        self.assert_call("PUT", "/revisions/cancel", json={"revisionIDs": ["r1"]})

    def test_revisions_list_requires_ids(self):
        with self.assertRaises(ValueError):
            self.client.api.revisions.list(file_id="f1")
        with self.assertRaises(ValueError):
            self.client.api.revisions.list(branch_id="b1")
        self.client.api.revisions.list("p1", None, "f1")
        self.assert_call("GET", "/projects/p1/branches/branch-main/files/f1/revisions")

    def test_branch_id_none_resolves(self):
        c = self.client
        c.api.commits.get("p1", None, "c1")
        self.assert_call("GET", "/projects/p1/branches/branch-main/commits/c1")
        c.api.files.move("p1", None, ["f1"], "parent-1")
        self.assert_call(
            "PUT",
            "/fileActions/move",
            json={"moveFiles": ["f1"], "newParentID": "parent-1"},
        )
        c.api.uploads.initiate("p1", None, [{"name": "x"}])
        self.assert_call("PUT", "/fileActions/initiateUpload", json={"files": [{"name": "x"}]})
        c.api.checkouts.checkout("p1", None, ["f1"])
        self.assert_call("PUT", "/fileActions/checkout", json={"fileIDs": ["f1"]})
        c.api.shared_links.create_live("p1", None, "Review Link", ["f1"])
        self.assert_call(
            "POST", "/files/sharedLink", json={"name": "Review Link", "fileIDs": ["f1"]}
        )
        c.api.metadata.get("p1", None, "f1")
        self.assert_call("GET", "/files/f1/metadata")
        c.api.revisions.get_closure("p1", None, "f1")
        self.assert_call("GET", "/files/f1/closure")
        c.api.boms.list("p1")
        self.assert_call("GET", "/projects/p1/branches/branch-main/boms")

    def test_approvals(self):
        c = self.client
        c.api.approvals.list()
        self.assert_call("GET", "/approvals")
        c.api.approvals.list("p1")
        self.assert_call("GET", "/projects/p1/approvals")
        c.api.approvals.get("p1", "a1")
        self.assert_call("GET", "/approvals/a1")
        c.api.approvals.close("p1", "a1", "approved")
        self.assert_call("PUT", "/approvals/a1/close", params={"status": "approved"})
        self.assertIsNone(self.last()["json"])

    def test_boms(self):
        c = self.client
        c.api.boms.list("p1", "b1")
        self.assert_call("GET", "/projects/p1/branches/b1/boms")
        c.api.boms.get("p1", "b1", "bom1")
        self.assert_call("GET", "/boms/bom1")
        c.api.boms.download(
            "p1",
            "b1",
            "bom1",
            {"versionId": "v", "viewId": "w", "type": "Indented", "formats": {}},
        )
        self.assert_call(
            "POST",
            "/boms/bom1/download",
            json={"versionId": "v", "viewId": "w", "type": "Indented", "formats": {}},
        )

    def test_search(self):
        self.client.api.search.files("bolt")
        self.assert_call("PUT", "/search", json={"search_key": "bolt"})
        self.client.api.search.files("bolt", page_size=5, from_offset=10)
        self.assert_call(
            "PUT",
            "/search",
            json={"search_key": "bolt"},
            params={"pageSize": 5, "from": 10},
        )

    def test_webhooks(self):
        c = self.client
        c.api.webhooks.list()
        self.assert_call("GET", "/webhooks/subscriptions")
        c.api.webhooks.create({"eventType": "file.updated", "targetURL": "https://example.com"})
        self.assert_call(
            "POST",
            "/webhooks/subscriptions",
            json={"eventType": "file.updated", "targetURL": "https://example.com"},
        )
        c.api.webhooks.get("sub1")
        self.assert_call("GET", "/webhooks/subscriptions/sub1")
        c.api.webhooks.update("sub1", {"isActive": False})
        self.assert_call("PUT", "/webhooks/subscriptions/sub1", json={"isActive": False})
        c.api.webhooks.rotate_secret("sub1")
        self.assert_call("POST", "/rotate")
        self.assertIsNone(self.last()["json"])
        c.api.webhooks.delete("sub1")
        self.assert_call("DELETE", "/webhooks/subscriptions/sub1")


class TestRouteMethodCoverage(unittest.TestCase):
    def test_every_public_api_method_is_called(self):
        src = Path(__file__).read_text(encoding="utf-8")
        client = BildClient(token="test-token", session=RouteSession())
        missing: list[str] = []
        for name in _Resources.__annotations__:
            resource = getattr(client.api, name)
            for method_name, _fn in inspect.getmembers(
                type(resource), predicate=inspect.isfunction
            ):
                if method_name.startswith("_"):
                    continue
                needle = f"api.{name}.{method_name}("
                if needle not in src:
                    missing.append(needle)
        self.assertEqual(missing, [], f"Route tests missing calls: {missing}")


if __name__ == "__main__":
    unittest.main()
