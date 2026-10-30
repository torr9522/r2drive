import http.client
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def url_path(value):
    parsed = urllib.parse.urlsplit(value)
    return parsed.path + (("?" + parsed.query) if parsed.query else "")


class R2DriveHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.port = 18090
        env = os.environ.copy()
        env.update(
            R2_DRIVE_DATA=cls.temp.name,
            R2_DRIVE_HOST="127.0.0.1",
            R2_DRIVE_PORT=str(cls.port),
        )
        cls.server = subprocess.Popen(
            [sys.executable, "app.py"], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                status, _, _ = cls.request("GET", "/api/status")
                if status == 200:
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise RuntimeError("test server did not start")

        cls.password = secrets.token_urlsafe(18)
        status, headers, body = cls.request(
            "POST", "/api/initialize",
            json.dumps({"username": "admin", "password": cls.password}).encode(),
            {"Content-Type": "application/json"},
        )
        assert status == 200, body
        cls.cookie = headers["set-cookie"].split(";", 1)[0]

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=5)
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, body=None, headers=None, authenticated=False):
        conn = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=10)
        headers = dict(headers or {})
        if authenticated:
            headers["Cookie"] = cls.cookie
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        payload = response.read()
        result = response.status, {k.lower(): v for k, v in response.getheaders()}, payload
        conn.close()
        return result

    @classmethod
    def api(cls, method, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        status, response_headers, payload = cls.request(method, path, body, headers, True)
        parsed = json.loads(payload) if payload else None
        return status, response_headers, parsed

    @classmethod
    def upload(cls, path, filename, content, content_type, folder_id="root"):
        boundary = "----r2drive-" + uuid.uuid4().hex
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"folderId\"\r\n\r\n{folder_id}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        status, headers, payload = cls.request(
            "POST", path, body,
            {"Content-Type": f"multipart/form-data; boundary={boundary}"}, True,
        )
        return status, headers, json.loads(payload)

    def test_01_status_auth_and_secure_cookie(self):
        status, _, body = self.request("GET", "/api/me")
        self.assertEqual(status, 401)
        self.assertIn("请先登录", body.decode())
        status, headers, _ = self.request(
            "POST", "/api/login",
            json.dumps({"username": "admin", "password": self.password}).encode(),
            {"Content-Type": "application/json", "X-Forwarded-Proto": "https"},
        )
        self.assertEqual(status, 200)
        self.assertIn("Secure", headers["set-cookie"])

    def test_02_drive_upload_folder_and_range_statistics(self):
        status, _, folder = self.api("POST", "/api/drive/folders", {"name": "docs", "parentId": "root"})
        self.assertEqual(status, 200)
        content = b"0123456789abcdef"
        status, _, uploaded = self.upload("/api/upload", "sample.txt", content, "text/plain", folder["id"])
        self.assertEqual(status, 200)
        self.assertEqual(uploaded["folderId"], folder["id"])

        public_path = url_path(uploaded["publicUrl"])
        status, headers, body = self.request("HEAD", public_path)
        self.assertEqual((status, body), (200, b""))
        self.assertEqual(headers["accept-ranges"], "bytes")
        status, headers, body = self.request("GET", public_path, headers={"Range": "bytes=2-5"})
        self.assertEqual((status, body), (206, b"2345"))
        self.assertEqual(headers["content-range"], "bytes 2-5/16")
        status, _, _ = self.api("PATCH", f"/api/drive/files/{uploaded['id']}", {"downloadLimitBytes": 6})
        self.assertEqual(status, 200)
        status, _, _ = self.request("GET", public_path, headers={"Range": "bytes=0-3"})
        self.assertEqual(status, 403)
        self.api("PATCH", f"/api/drive/files/{uploaded['id']}", {"downloadLimitBytes": None})
        status, _, _ = self.request("GET", public_path, headers={"Range": "bytes=99-100"})
        self.assertEqual(status, 416)
        status, _, files = self.api("GET", f"/api/drive/files?folderId={folder['id']}")
        self.assertEqual(files[0]["downloadCount"], 0)
        self.assertEqual(files[0]["downloadBytes"], 4)
        status, _, body = self.request("GET", public_path)
        self.assertEqual((status, body), (200, content))
        _, _, files = self.api("GET", f"/api/drive/files?folderId={folder['id']}")
        self.assertEqual(files[0]["downloadCount"], 1)
        self.assertEqual(files[0]["downloadBytes"], 20)
        self.__class__.drive_file = files[0]
        self.__class__.drive_folder = folder

    def test_03_limit_private_delete_and_legacy_routes(self):
        file_row = self.drive_file
        status, _, renamed_folder = self.api(
            "PATCH", f"/api/drive/folders/{self.drive_folder['id']}", {"name": "renamed-docs"},
        )
        self.assertEqual((status, renamed_folder["name"]), (200, "renamed-docs"))
        status, _, renamed_file = self.api(
            "PATCH", f"/api/drive/files/{file_row['id']}", {"name": "renamed-sample.txt"},
        )
        self.assertEqual((status, renamed_file["name"]), (200, "renamed-sample.txt"))
        self.assertEqual(self.api("DELETE", f"/api/drive/folders/{self.drive_folder['id']}")[0], 409)
        status, _, updated = self.api(
            "PATCH", f"/api/drive/files/{file_row['id']}", {"downloadLimitBytes": 20},
        )
        self.assertEqual(status, 200)
        status, _, _ = self.request("GET", url_path(updated["publicUrl"]))
        self.assertEqual(status, 403)
        status, _, private = self.api(
            "PATCH", f"/api/drive/files/{file_row['id']}/public", {"isPublic": False},
        )
        self.assertFalse(private["isPublic"])
        token_path = url_path(file_row["publicUrl"])
        self.assertEqual(self.request("GET", token_path)[0], 404)
        status, _, public = self.api(
            "PATCH", f"/api/drive/files/{file_row['id']}/public", {"isPublic": True},
        )
        self.assertEqual(self.request("GET", url_path(public["shareUrl"]))[0], 200)
        self.assertEqual(self.request("GET", url_path(public["publicUrl"]) + "/sample.txt")[0], 403)
        self.assertEqual(self.api("DELETE", f"/api/drive/files/{file_row['id']}")[0], 200)
        self.assertEqual(self.request("GET", url_path(public["publicUrl"]))[0], 404)

    def test_04_image_validation_and_category_isolation(self):
        status, _, image_folder = self.api("POST", "/api/image-host/folders", {"name": "gallery", "parentId": "root"})
        self.assertEqual(status, 200)
        png = b"\x89PNG\r\n\x1a\n" + b"minimal-test-data"
        status, _, image = self.upload("/api/image-host/upload", "image.png", png, "image/png")
        self.assertEqual(status, 200)
        self.assertEqual(image["fileCategory"], "image_host")
        status, _, error = self.upload("/api/image-host/upload", "bad.png", b"not-png", "image/png")
        self.assertEqual(status, 400)
        self.assertIn("不支持", error["error"])
        self.assertEqual(self.api("PATCH", f"/api/drive/files/{image['id']}", {"name": "escape.png"})[0], 404)
        status, _, moved = self.api(
            "POST", "/api/image-host/files/batch-move", {"ids": [image["id"]], "folderId": image_folder["id"]},
        )
        self.assertEqual((status, moved["moved"]), (200, [image["id"]]))
        status, _, skipped = self.api(
            "POST", "/api/image-host/files/batch-move", {"ids": [image["id"]], "folderId": image_folder["id"]},
        )
        self.assertEqual((status, skipped["skipped"]), (200, [image["id"]]))
        self.assertEqual(
            self.api("POST", "/api/image-host/files/batch-move", {"ids": [image["id"]], "folderId": self.drive_folder["id"]})[0],
            404,
        )
        status, _, listed = self.api("GET", f"/api/image-host/files?folderId={image_folder['id']}")
        self.assertEqual((status, [item["id"] for item in listed]), (200, [image["id"]]))
        status, _, deleted = self.api("POST", "/api/image-host/files/batch-delete", {"ids": [image["id"]]})
        self.assertEqual((status, deleted["deleted"]), (200, [image["id"]]))
        self.assertEqual(self.api("DELETE", f"/api/image-host/folders/{image_folder['id']}")[0], 200)

        db_path = Path(self.temp.name) / "drive.sqlite3"
        with sqlite3.connect(db_path) as conn:
            token = secrets.token_urlsafe(24)
            conn.execute(
                "INSERT INTO folders (id,user_id,parent_id,name,share_token,folder_category,created_at,updated_at) "
                "SELECT ?,id,'root','images',?,'image_host',1,1 FROM users LIMIT 1",
                (str(uuid.uuid4()), token),
            )
        self.assertEqual(self.request("GET", f"/share/folder/{token}")[0], 404)

    def test_05_folder_share_and_nonempty_delete(self):
        folder = self.drive_folder
        status, _, shared = self.api(
            "PATCH", f"/api/drive/folders/{folder['id']}/public", {"isPublic": True},
        )
        self.assertEqual(status, 200)
        self.assertEqual(self.request("GET", url_path(shared["shareUrl"]))[0], 200)
        self.assertEqual(self.api("DELETE", f"/api/drive/folders/{folder['id']}")[0], 200)

    def test_06_legacy_database_migration_preserves_rows(self):
        with tempfile.TemporaryDirectory() as data_dir:
            db_path = Path(data_dir) / "drive.sqlite3"
            with sqlite3.connect(db_path) as conn:
                conn.executescript(
                    """
                    CREATE TABLE folders (
                      id TEXT PRIMARY KEY, user_id TEXT NOT NULL, parent_id TEXT NOT NULL,
                      name TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
                    );
                    CREATE TABLE files (
                      id TEXT PRIMARY KEY, user_id TEXT NOT NULL, folder_id TEXT NOT NULL,
                      name TEXT NOT NULL, storage_path TEXT NOT NULL, size INTEGER NOT NULL,
                      content_type TEXT NOT NULL, is_public INTEGER NOT NULL DEFAULT 0,
                      share_token TEXT UNIQUE, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
                    );
                    INSERT INTO folders VALUES ('old-folder','old-user','root','legacy',1,1);
                    INSERT INTO files VALUES ('old-file','old-user','old-folder','legacy.txt','/tmp/legacy',1,'text/plain',0,NULL,1,1);
                    """
                )
            env = os.environ.copy()
            env["R2_DRIVE_DATA"] = data_dir
            subprocess.run(
                [sys.executable, "-c", "import app; app.init_db()"],
                cwd=ROOT, env=env, check=True,
            )
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT folder_category FROM folders WHERE id='old-folder'").fetchone()[0], "drive")
                row = conn.execute("SELECT file_category, download_count, download_bytes FROM files WHERE id='old-file'").fetchone()
                self.assertEqual(row, ("drive", 0, 0))
                self.assertEqual(conn.execute("SELECT sort_order FROM folders WHERE id='old-folder'").fetchone()[0], 0)
                self.assertEqual(conn.execute("SELECT sort_order FROM files WHERE id='old-file'").fetchone()[0], 0)

    def test_07_grouped_sorting_is_scoped_and_persistent(self):
        folders = []
        for name in ("sort-a", "sort-b", "sort-c"):
            status, _, folder = self.api("POST", "/api/drive/folders", {"name": name, "parentId": "root"})
            self.assertEqual(status, 200)
            folders.append(folder)
        status, _, child = self.api("POST", "/api/drive/folders", {"name": "sort-child", "parentId": folders[0]["id"]})
        self.assertEqual(status, 200)

        files = []
        for name in ("sort-1.txt", "sort-2.txt", "sort-3.txt"):
            status, _, row = self.upload("/api/upload", name, name.encode(), "text/plain")
            self.assertEqual(status, 200)
            files.append(row)
        child_files = []
        for name in ("child-1.txt", "child-2.txt"):
            status, _, row = self.upload("/api/upload", name, name.encode(), "text/plain", folders[0]["id"])
            self.assertEqual(status, 200)
            child_files.append(row)

        folder_order = [folders[2]["id"], folders[0]["id"], folders[1]["id"]]
        status, _, result = self.api("POST", "/api/items/reorder", {
            "category": "drive", "itemType": "folder", "parentId": "root", "ids": folder_order,
        })
        self.assertEqual((status, result["ids"]), (200, folder_order))
        file_order = [files[2]["id"], files[0]["id"], files[1]["id"]]
        self.assertEqual(self.api("POST", "/api/items/reorder", {
            "category": "drive", "itemType": "file", "parentId": "root", "ids": file_order,
        })[0], 200)
        child_order = [child_files[1]["id"], child_files[0]["id"]]
        self.assertEqual(self.api("POST", "/api/items/reorder", {
            "category": "drive", "itemType": "file", "parentId": folders[0]["id"], "ids": child_order,
        })[0], 200)

        _, _, listed_folders = self.api("GET", "/api/drive/folders")
        self.assertEqual([row["id"] for row in listed_folders if row["parentId"] == "root"], folder_order)
        _, _, listed_files = self.api("GET", "/api/drive/files?folderId=root")
        self.assertEqual([row["id"] for row in listed_files], file_order)
        _, _, listed_child_files = self.api("GET", f"/api/drive/files?folderId={folders[0]['id']}")
        self.assertEqual([row["id"] for row in listed_child_files], child_order)
        self.assertEqual(self.api("POST", "/api/items/reorder", {
            "category": "drive", "itemType": "file", "parentId": "root", "ids": file_order[:-1],
        })[0], 409)
        self.assertEqual(self.api("POST", "/api/items/reorder", {
            "category": "image_host", "itemType": "file", "parentId": "root", "ids": file_order,
        })[0], 409)

        db_path = Path(self.temp.name) / "drive.sqlite3"
        with sqlite3.connect(db_path) as conn:
            persisted = [row[0] for row in conn.execute(
                "SELECT id FROM files WHERE file_category='drive' AND folder_id='root' ORDER BY sort_order, id"
            )]
        self.assertEqual(persisted, file_order)
        self.__class__.sort_folders = folders
        self.__class__.sort_child = child
        self.__class__.sort_files = files
        self.__class__.sort_child_files = child_files

    def test_08_mixed_move_conflicts_cycles_and_compatibility(self):
        folders = self.sort_folders
        child = self.sort_child
        source = folders[0]
        target = folders[1]
        child_file = self.sort_child_files[0]

        _, _, before_files = self.api("GET", f"/api/drive/files?folderId={source['id']}")
        before = next(row for row in before_files if row["id"] == child_file["id"])
        public_path = url_path(before["publicUrl"])
        status, _, payload = self.request("GET", public_path)
        self.assertEqual((status, payload), (200, b"child-1.txt"))
        deadline = time.time() + 2
        while time.time() < deadline:
            _, _, rows = self.api("GET", f"/api/drive/files?folderId={source['id']}")
            current = next(row for row in rows if row["id"] == before["id"])
            if current["downloadCount"] >= 1:
                break
            time.sleep(0.02)
        self.assertGreaterEqual(current["downloadCount"], 1)
        db_path = Path(self.temp.name) / "drive.sqlite3"
        with sqlite3.connect(db_path) as conn:
            storage_before = conn.execute("SELECT storage_path FROM files WHERE id=?", (before["id"],)).fetchone()[0]

        status, _, moved = self.api("POST", "/api/items/move", {
            "category": "drive",
            "items": [{"type": "folder", "id": source["id"]}, {"type": "file", "id": before["id"]}],
            "folderId": target["id"],
            "conflictPolicy": "cancel",
        })
        self.assertEqual(status, 200)
        self.assertEqual([row["id"] for row in moved["moved"]], [source["id"]])
        self.assertEqual(moved["skipped"][0]["reason"], "covered_by_parent")
        _, _, moved_folders = self.api("GET", "/api/drive/folders")
        moved_source = next(row for row in moved_folders if row["id"] == source["id"])
        self.assertEqual((moved_source["parentId"], moved_source["shareUrl"]), (target["id"], source["shareUrl"]))
        _, _, target_files = self.api("GET", f"/api/drive/files?folderId={source['id']}")
        after = next(row for row in target_files if row["id"] == before["id"])
        self.assertEqual((after["id"], after["publicUrl"], after["downloadCount"]), (before["id"], before["publicUrl"], current["downloadCount"]))
        with sqlite3.connect(db_path) as conn:
            storage_after = conn.execute("SELECT storage_path FROM files WHERE id=?", (before["id"],)).fetchone()[0]
        self.assertEqual(storage_after, storage_before)
        self.assertEqual(self.request("GET", public_path, headers={"Range": "bytes=0-4"})[:1], (206,))
        self.assertEqual(self.request("GET", public_path + "/legacy-name.txt")[0], 200)
        folder_download = url_path(source["shareUrl"]) + f"/file/{before['id']}/download"
        self.assertEqual(self.request("GET", folder_download)[0], 200)
        status, _, moved_out = self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": before["id"]}],
            "folderId": "root", "conflictPolicy": "cancel",
        })
        self.assertEqual((status, moved_out["moved"][0]["id"]), (200, before["id"]))
        self.assertEqual(self.request("GET", folder_download)[0], 404)
        self.assertEqual(self.request("GET", public_path)[0], 200)
        self.assertEqual(self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": before["id"]}],
            "folderId": source["id"], "conflictPolicy": "cancel",
        })[0], 200)

        status, _, cycle = self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "folder", "id": target["id"]}],
            "folderId": child["id"], "conflictPolicy": "cancel",
        })
        self.assertEqual(status, 200)
        self.assertEqual(cycle["failed"][0]["reason"], "cycle")

        status, _, conflict_target = self.api("POST", "/api/drive/folders", {"name": "conflicts", "parentId": "root"})
        self.assertEqual(status, 200)
        _, _, existing = self.upload("/api/upload", "same.txt", b"target", "text/plain", conflict_target["id"])
        _, _, cancel_source = self.upload("/api/upload", "same.txt", b"source", "text/plain")
        cancel_request = {"category": "drive", "items": [{"type": "file", "id": cancel_source["id"]}], "folderId": conflict_target["id"], "conflictPolicy": "cancel"}
        self.assertEqual(self.api("POST", "/api/items/move", cancel_request)[0], 409)
        _, _, root_after_cancel = self.api("GET", "/api/drive/files?folderId=root")
        self.assertIn(cancel_source["id"], [row["id"] for row in root_after_cancel])
        cancel_request["conflictPolicy"] = "skip"
        status, _, skipped = self.api("POST", "/api/items/move", cancel_request)
        self.assertEqual((status, skipped["skipped"][0]["reason"]), (200, "name_conflict"))
        cancel_request["conflictPolicy"] = "rename"
        status, _, renamed = self.api("POST", "/api/items/move", cancel_request)
        self.assertEqual((status, renamed["moved"][0]["name"]), (200, "same (1).txt"))
        _, _, conflict_files = self.api("GET", f"/api/drive/files?folderId={conflict_target['id']}")
        self.assertEqual([row["id"] for row in conflict_files][-2:], [existing["id"], cancel_source["id"]])

        _, _, rollback_file = self.upload("/api/upload", "rollback.txt", b"rollback", "text/plain")
        _, _, second_conflict = self.upload("/api/upload", "same.txt", b"second", "text/plain")
        self.assertEqual(self.api("POST", "/api/items/move", {
            "category": "drive",
            "items": [{"type": "file", "id": rollback_file["id"]}, {"type": "file", "id": second_conflict["id"]}],
            "folderId": conflict_target["id"], "conflictPolicy": "cancel",
        })[0], 409)
        _, _, root_after_rollback = self.api("GET", "/api/drive/files?folderId=root")
        self.assertTrue({rollback_file["id"], second_conflict["id"]}.issubset({row["id"] for row in root_after_rollback}))
        status, _, same_folder = self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": rollback_file["id"]}],
            "folderId": "root", "conflictPolicy": "skip",
        })
        self.assertEqual((status, same_folder["skipped"][0]["reason"]), (200, "same_folder"))
        self.assertEqual(self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": rollback_file["id"]}],
            "folderId": "missing-folder", "conflictPolicy": "skip",
        })[0], 404)
        status, _, missing_source = self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": "missing-file"}],
            "folderId": "root", "conflictPolicy": "skip",
        })
        self.assertEqual((status, missing_source["failed"][0]["reason"]), (200, "not_found"))

        _, _, folder_conflict_target = self.api("POST", "/api/drive/folders", {"name": "folder-target", "parentId": "root"})
        _, _, target_named = self.api("POST", "/api/drive/folders", {"name": "duplicate-folder", "parentId": folder_conflict_target["id"]})
        _, _, source_named = self.api("POST", "/api/drive/folders", {"name": "duplicate-folder", "parentId": "root"})
        status, _, renamed_folder = self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "folder", "id": source_named["id"]}],
            "folderId": folder_conflict_target["id"], "conflictPolicy": "rename",
        })
        self.assertEqual((status, renamed_folder["moved"][0]["name"]), (200, "duplicate-folder (1)"))
        self.assertNotEqual(target_named["id"], source_named["id"])

        status, _, image_folder = self.api("POST", "/api/image-host/folders", {"name": "image-only", "parentId": "root"})
        self.assertEqual(status, 200)
        self.assertEqual(self.api("POST", "/api/items/move", {
            "category": "drive", "items": [{"type": "file", "id": existing["id"]}],
            "folderId": image_folder["id"], "conflictPolicy": "skip",
        })[0], 404)

    def test_09_image_folder_move_and_sorting(self):
        status, _, first = self.api("POST", "/api/image-host/folders", {"name": "gallery-a", "parentId": "root"})
        self.assertEqual(status, 200)
        status, _, second = self.api("POST", "/api/image-host/folders", {"name": "gallery-b", "parentId": "root"})
        self.assertEqual(status, 200)
        status, _, nested = self.api("POST", "/api/image-host/folders", {"name": "nested", "parentId": first["id"]})
        self.assertEqual(status, 200)
        png = b"\x89PNG\r\n\x1a\n" + b"move-image"
        status, _, image = self.upload("/api/image-host/upload", "move.png", png, "image/png", nested["id"])
        self.assertEqual(status, 200)
        status, _, result = self.api("POST", "/api/items/move", {
            "category": "image_host", "items": [{"type": "folder", "id": nested["id"]}, {"type": "file", "id": image["id"]}],
            "folderId": second["id"], "conflictPolicy": "cancel",
        })
        self.assertEqual(status, 200)
        self.assertEqual(result["moved"][0]["id"], nested["id"])
        self.assertEqual(result["skipped"][0]["reason"], "covered_by_parent")
        self.assertEqual(self.request("GET", url_path(image["publicUrl"]))[0], 200)
        _, _, all_folders = self.api("GET", "/api/image-host/folders")
        root_ids = [row["id"] for row in all_folders if row["parentId"] == "root"]
        reversed_ids = list(reversed(root_ids))
        self.assertEqual(self.api("POST", "/api/items/reorder", {
            "category": "image_host", "itemType": "folder", "parentId": "root", "ids": reversed_ids,
        })[0], 200)
        _, _, all_folders = self.api("GET", "/api/image-host/folders")
        self.assertEqual([row["id"] for row in all_folders if row["parentId"] == "root"], reversed_ids)


if __name__ == "__main__":
    unittest.main(verbosity=2)
