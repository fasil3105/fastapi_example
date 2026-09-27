"""HTTP integration tests using SQLite and mocked object storage.

Run from this directory with: python -m unittest discover -s tests -v
"""
import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image
from botocore.exceptions import ClientError
from pypdf import PdfWriter
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.security import hash_password, verify_password
from app.db.database import get_session
from app.main import app
from app.schemas.user import UserCreate


class UnitTests(unittest.TestCase):
    def test_password_hash_verifies_only_matching_password(self):
        hashed = hash_password("TestPass1!")
        self.assertNotEqual(hashed, "TestPass1!")
        self.assertTrue(verify_password("TestPass1!", hashed))
        self.assertFalse(verify_password("WrongPass1!", hashed))

    def test_user_schema_rejects_weak_password(self):
        with self.assertRaises(ValueError):
            UserCreate(name="Test", email="test@example.com", password="weak")

    def test_user_schema_accepts_strong_password(self):
        user = UserCreate(name="Test", email="test@example.com", password="StrongPass1!")
        self.assertEqual(user.email, "test@example.com")

    def test_user_schema_rejects_invalid_email(self):
        with self.assertRaises(ValueError):
            UserCreate(name="Test", email="not-an-email", password="StrongPass1!")


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        SQLModel.metadata.create_all(self.engine)

        def test_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = test_session
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        SQLModel.metadata.drop_all(self.engine)
        self.engine.dispose()

    def register(self, email="alice@example.com"):
        return self.client.post(
            "/auth/register",
            json={"name": "Alice", "email": email, "password": "StrongPass1!"},
        )

    def login(self, email="alice@example.com"):
        return self.client.post(
            "/auth/login", data={"username": email, "password": "StrongPass1!"}
        )

    def auth_headers(self, email="alice@example.com"):
        if self.login(email).status_code != 200:
            self.register(email)
        token = self.login(email).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def create_file(self, email="alice@example.com"):
        self.register(email)
        headers = self.auth_headers(email)
        with Session(self.engine) as session:
            from app.models.file import FileMetadata
            from app.models.users import Users

            owner = session.exec(select(Users).where(Users.email == email)).first()
            file = FileMetadata(
                user_id=owner.id, original_filename="a.png", stored_filename="a.png",
                storage_key="uploads/a.png", file_type="image/png", file_size=10, status="VALID",
            )
            session.add(file)
            session.commit()
            session.refresh(file)
            return headers, file.id

    def test_register_login_and_authenticated_file_listing(self):
        registered = self.register()
        self.assertEqual(registered.status_code, 200, registered.text)
        self.assertNotIn("password", registered.json())

        logged_in = self.login()
        self.assertEqual(logged_in.status_code, 200, logged_in.text)
        token = logged_in.json()["access_token"]
        files = self.client.get("/files/files", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(files.status_code, 200, files.text)
        self.assertEqual(files.json(), {"files": []})

    def test_duplicate_registration_and_invalid_login_are_rejected(self):
        self.assertEqual(self.register().status_code, 200)
        self.assertEqual(self.register().status_code, 409)
        response = self.client.post(
            "/auth/login", data={"username": "alice@example.com", "password": "incorrect"}
        )
        self.assertEqual(response.status_code, 401)

    def test_upload_stores_valid_image_and_rejects_extension_mismatch(self):
        self.register()
        token = self.login().json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        image_data = BytesIO()
        Image.new("RGB", (2, 2), color="red").save(image_data, format="PNG")
        image_data.seek(0)
        with patch("app.routes.files.s3_client.put_object") as put_object:
            uploaded = self.client.post(
                "/files/uploadfile/", headers=headers,
                files={"file": ("picture.png", image_data.getvalue(), "image/png")},
            )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        put_object.assert_called_once()
        self.assertEqual(uploaded.json()["Allowed"]["MIME_type"], "image/png")

        mismatch = self.client.post(
            "/files/uploadfile/", headers=headers,
            files={"file": ("picture.jpg", image_data.getvalue(), "image/png")},
        )
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn("does not match", mismatch.json()["detail"])

    def test_file_metadata_is_private_to_owner(self):
        self.register()
        first_token = self.login().json()["access_token"]
        with Session(self.engine) as session:
            from app.models.file import FileMetadata
            from app.models.users import Users

            owner = session.exec(__import__("sqlmodel").select(Users)).first()
            file = FileMetadata(
                user_id=owner.id, original_filename="a.png", stored_filename="a.png",
                storage_key="uploads/a.png", file_type="image/png", file_size=10, status="VALID",
            )
            session.add(file)
            session.commit()
            session.refresh(file)
            file_id = file.id

        self.register("bob@example.com")
        second_token = self.login("bob@example.com").json()["access_token"]
        response = self.client.get(
            f"/files/files/{file_id}", headers={"Authorization": f"Bearer {second_token}"}
        )
        self.assertEqual(response.status_code, 403)

    def test_authentication_rejects_missing_and_invalid_tokens(self):
        self.assertEqual(self.client.get("/files/files").status_code, 401)
        self.assertEqual(
            self.client.get("/files/files", headers={"Authorization": "Bearer invalid"}).status_code,
            401,
        )

    def test_file_metadata_returns_file_and_not_found(self):
        headers, file_id = self.create_file()
        response = self.client.get(f"/files/files/{file_id}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["files"]["original_filename"], "a.png")
        self.assertEqual(self.client.get("/files/files/999", headers=headers).status_code, 404)

    def test_download_returns_presigned_url_and_checks_access(self):
        headers, file_id = self.create_file()
        with patch("app.routes.files.generate_presigned_url", return_value="https://storage/file") as signer:
            response = self.client.get(f"/files/files/{file_id}/download", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["download_url"], "https://storage/file")
        signer.assert_called_once_with("uploads/a.png")
        self.assertEqual(self.client.get("/files/files/999/download", headers=headers).status_code, 404)

        other_headers = self.auth_headers("bob@example.com")
        self.assertEqual(
            self.client.get(f"/files/files/{file_id}/download", headers=other_headers).status_code, 403
        )

    def test_delete_removes_storage_and_metadata(self):
        headers, file_id = self.create_file()
        with patch("app.routes.files.delete_file_in_storage", return_value=True) as delete_storage:
            response = self.client.delete(f"/files/delete/{file_id}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["message"], "File deleted successfully")
        delete_storage.assert_called_once_with("uploads/a.png")
        self.assertEqual(self.client.get(f"/files/files/{file_id}", headers=headers).status_code, 404)
        self.assertEqual(self.client.delete("/files/delete/999", headers=headers).status_code, 404)

    def test_delete_checks_owner_and_preserves_metadata_when_storage_fails(self):
        owner_headers, file_id = self.create_file()
        other_headers = self.auth_headers("bob@example.com")
        self.assertEqual(
            self.client.delete(f"/files/delete/{file_id}", headers=other_headers).status_code, 403
        )
        storage_error = ClientError(
            {"Error": {"Code": "InternalError", "Message": "failed"}}, "DeleteObject"
        )
        with patch("app.routes.files.delete_file_in_storage", side_effect=storage_error):
            response = self.client.delete(f"/files/delete/{file_id}", headers=owner_headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.client.get(f"/files/files/{file_id}", headers=owner_headers).status_code, 200)

    def test_upload_accepts_valid_pdf(self):
        headers = self.auth_headers()
        pdf = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(pdf)
        with patch("app.routes.files.s3_client.put_object") as put_object:
            response = self.client.post(
                "/files/uploadfile/", headers=headers,
                files={"file": ("document.pdf", pdf.getvalue(), "application/pdf")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["Allowed"]["MIME_type"], "application/pdf")
        put_object.assert_called_once()

    def test_upload_rejects_unsupported_empty_oversized_and_corrupt_files(self):
        headers = self.auth_headers()
        cases = [
            ("notes.txt", b"text", 400),
            ("empty.png", b"", 400),
            ("large.png", b"x" * (2 * 1024 * 1024 + 1), 413),
            ("broken.png", b"\x89PNG\r\n\x1a\nnot-an-image", 400),
            ("broken.pdf", b"%PDF-invalid", 400),
        ]
        for filename, content, expected_status in cases:
            with self.subTest(filename=filename):
                response = self.client.post(
                    "/files/uploadfile/", headers=headers,
                    files={"file": (filename, content, "application/octet-stream")},
                )
                self.assertEqual(response.status_code, expected_status, response.text)

    def test_upload_storage_error_returns_server_error(self):
        headers = self.auth_headers()
        image_data = BytesIO()
        Image.new("RGB", (2, 2), color="red").save(image_data, format="PNG")
        with patch("app.routes.files.s3_client.put_object", side_effect=RuntimeError("offline")):
            response = self.client.post(
                "/files/uploadfile/", headers=headers,
                files={"file": ("picture.png", image_data.getvalue(), "image/png")},
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to upload file to storage")

