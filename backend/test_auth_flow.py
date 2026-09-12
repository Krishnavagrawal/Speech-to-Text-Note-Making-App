from fastapi.testclient import TestClient
import pytest

from main import app
from services.transcription_report import build_transcription_report


def test_register_and_login_flow():
    client = TestClient(app)
    email = "auth-test@example.com"
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


def test_forgot_password_returns_local_otp_when_email_send_fails(monkeypatch):
    client = TestClient(app)
    email = "local-otp@example.com"
    register_payload = {
        "name": "Local OTP User",
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
    assert payload["email_delivery_failed"] is True
    assert "otp" in payload
    assert len(payload["otp"]) == 6


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
