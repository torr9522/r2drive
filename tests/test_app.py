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


if __name__ == "__main__":
    unittest.main(verbosity=2)
