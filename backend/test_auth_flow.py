from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from main import app
from services.transcription_report import build_transcription_report


def test_register_and_login_flow():
    client = TestClient(app)
    email = f"auth-test-{uuid4().hex}@example.com"
    payload = {
        "name": "Test User",
        "email": email,
        "password": "StrongPass123!",
    }

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201, register_response.text
    register_data = register_response.json()
    assert "token" in register_data
    assert register_data["user"]["email"] == email

    login_response = client.post("/auth/login", json={
        "email": email,
        "password": "StrongPass123!",
    })
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["token"]

    notes_response = client.get("/notes", headers={"Authorization": f"Bearer {token}"})
    assert notes_response.status_code == 200, notes_response.text


def test_register_duplicate_email_returns_account_exists_message():
    client = TestClient(app)
    email = f"duplicate-{uuid4().hex}@example.com"
    payload = {
        "name": "Duplicate User",
        "email": email,
        "password": "StrongPass123!",
    }

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Account already exists. Please login."


def test_register_welcome_mail_failure_is_non_blocking(monkeypatch):
    client = TestClient(app)
    email = f"welcome-failure-{uuid4().hex}@example.com"
    payload = {
        "name": "Welcome Failure User",
        "email": email,
        "password": "StrongPass123!",
    }

    def raise_welcome_failure(_name: str, _email: str):
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr("main.send_welcome_email", raise_welcome_failure)

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["user"]["email"] == email
    assert response.json()["message"] == "Account created successfully. Welcome email could not be sent right now."


def test_forgot_password_returns_generic_message_when_email_send_fails(monkeypatch):
    client = TestClient(app)
    email = f"secure-otp-{uuid4().hex}@example.com"
    register_payload = {
        "name": "Secure OTP User",
        "email": email,
        "password": "StrongPass123!",
    }

    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201, register_response.text

    def raise_smtp_timeout(_email: str, _otp: str):
        raise RuntimeError("Connection unexpectedly closed: The read operation timed out")

    monkeypatch.setattr("main.send_reset_otp", raise_smtp_timeout)

    response = client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "If an account exists, a reset code has been sent."
    assert "email_delivery_failed" not in payload
    assert "otp" not in payload


def test_build_transcription_report_produces_confidence_and_accuracy():
    report = build_transcription_report(
        segments=[
            {"start": 0.0, "end": 1.0, "text": "hello world", "language": "en", "confidence": 0.91},
            {"start": 1.0, "end": 2.0, "text": "how are you", "language": "en", "confidence": 0.87},
        ],
        detected_languages=["English"],
    )

    assert report["confidence_score"] == pytest.approx(0.89, abs=0.01)
    assert report["accuracy_percent"] == pytest.approx(89.0, abs=0.01)
    assert report["language_count"] == 1
    assert report["word_count"] == 5
    assert report["segments_processed"] == 2
