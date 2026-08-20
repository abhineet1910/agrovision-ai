import io
from unittest.mock import patch


def _login(client, registered_user):
    return client.post("/auth/login", data=registered_user, follow_redirects=True)


def test_scan_requires_login(client):
    resp = client.post("/api/scan", data={})
    assert resp.status_code in (302, 401)  # redirected to login (flask-login default)


def test_scan_rejects_missing_file(client, registered_user):
    _login(client, registered_user)
    resp = client.post("/api/scan", data={})
    assert resp.status_code == 400
    assert "No image file" in resp.get_json()["error"]


@patch("app.routes.api.analyze_crop_image")
def test_scan_success_returns_diagnosis(mock_analyze, client, registered_user):
    mock_analyze.return_value = {
        "diseaseName": "Powdery Mildew",
        "severity": "Medium",
        "confidence": 0.82,
        "description": "White fungal patches on leaves.",
        "treatments": ["Apply sulfur spray", "Improve air circulation"],
        "fertilizer": {"name": "Balanced NPK", "dosage": "30g/plant", "schedule": "Monthly"},
    }
    _login(client, registered_user)

    data = {"image": (io.BytesIO(b"fake-image-bytes"), "leaf.jpg")}
    resp = client.post("/api/scan", data=data, content_type="multipart/form-data")

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["diseaseName"] == "Powdery Mildew"
    assert body["severity"] == "Medium"


@patch("app.routes.api.chat_reply")
def test_chat_success(mock_reply, client, registered_user):
    mock_reply.return_value = "Water your tomatoes early in the morning."
    _login(client, registered_user)

    resp = client.post("/api/chat", json={"message": "When should I water tomatoes?"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["reply"]["role"] == "model"
    assert "morning" in body["reply"]["text"]


def test_chat_rejects_empty_message(client, registered_user):
    _login(client, registered_user)
    resp = client.post("/api/chat", json={"message": "  "})
    assert resp.status_code == 400
