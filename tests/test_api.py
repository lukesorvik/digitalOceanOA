import os
from pathlib import Path

from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["UPLOAD_DIR"] = str(upload_dir)
    os.environ["SIGNING_SECRET"] = "test-secret"

    from app.main import create_app

    app = create_app()
    return TestClient(app)


def test_upload_and_list_metadata(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "100"},
            files={"file": ("notes.txt", b"hello-world", "text/plain")},
        )
        assert upload_response.status_code == 201
        upload_data = upload_response.json()

        list_response = client.get("/files", headers={"X-User-Id": "100"})
        assert list_response.status_code == 200
        listed_files = list_response.json()
        assert len(listed_files) == 1
        assert listed_files[0]["file_id"] == upload_data["file_id"]
        assert listed_files[0]["filename"] == "notes.txt"
        assert listed_files[0]["size_bytes"] == 11


def test_signed_url_download_and_audit(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "42"},
            files={"file": ("private.txt", b"secret-content", "text/plain")},
        )
        file_id = upload_response.json()["file_id"]

        sign_response = client.post(
            f"/files/{file_id}/signed-link",
            headers={"X-User-Id": "42"},
            json={"ttl_seconds": 600},
        )
        assert sign_response.status_code == 200
        signed_url = sign_response.json()["download_url"]

        token = signed_url.rsplit("/", 1)[1]
        download_response = client.get(f"/download/{token}")
        assert download_response.status_code == 200
        assert download_response.content == b"secret-content"

        from app.database import SessionLocal
        from app.models import LinkAudit

        with SessionLocal() as session:
            audit_count = session.query(LinkAudit).count()
            assert audit_count == 1


def test_signed_link_owner_only(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "7"},
            files={"file": ("owner.txt", b"owner-data", "text/plain")},
        )
        file_id = upload_response.json()["file_id"]

        forbidden_sign_response = client.post(
            f"/files/{file_id}/signed-link",
            headers={"X-User-Id": "9"},
            json={"ttl_seconds": 600},
        )
        assert forbidden_sign_response.status_code == 404


def test_delete_file_removes_metadata_and_disk_file(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "12"},
            files={"file": ("delete-me.txt", b"delete-me-content", "text/plain")},
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        from app.database import SessionLocal
        from app.models import StoredFile

        with SessionLocal() as session:
            stored_file = session.query(StoredFile).filter(StoredFile.id == file_id).first()
            assert stored_file is not None
            disk_path = Path(stored_file.upload_path)
            assert disk_path.exists()

        delete_response = client.delete(f"/files/{file_id}", headers={"X-User-Id": "12"})
        assert delete_response.status_code == 204

        with SessionLocal() as session:
            stored_file_after_delete = session.query(StoredFile).filter(StoredFile.id == file_id).first()
            assert stored_file_after_delete is None

        assert not disk_path.exists()


def test_delete_file_owner_only(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "18"},
            files={"file": ("owner-delete.txt", b"owner-delete", "text/plain")},
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        forbidden_delete = client.delete(f"/files/{file_id}", headers={"X-User-Id": "19"})
        assert forbidden_delete.status_code == 404


def test_list_user_link_audits(tmp_path: Path):
    with build_client(tmp_path) as client:
        upload_response = client.post(
            "/files/upload",
            headers={"X-User-Id": "25"},
            files={"file": ("audit-me.txt", b"audit-me", "text/plain")},
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        sign_response = client.post(
            f"/files/{file_id}/signed-link",
            headers={"X-User-Id": "25"},
            json={"ttl_seconds": 123},
        )
        assert sign_response.status_code == 200

        audit_list_response = client.get("/files/users/25/link-audits", headers={"X-User-Id": "25"})
        assert audit_list_response.status_code == 200
        audits = audit_list_response.json()
        assert len(audits) == 1
        assert audits[0]["file_id"] == file_id
        assert audits[0]["filename"] == "audit-me.txt"
        assert audits[0]["requester_user_id"] == 25
        assert audits[0]["ttl_seconds"] == 123


def test_list_user_link_audits_forbidden_when_user_mismatch(tmp_path: Path):
    with build_client(tmp_path) as client:
        forbidden_response = client.get("/files/users/99/link-audits", headers={"X-User-Id": "98"})
        assert forbidden_response.status_code == 403
