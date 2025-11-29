from fastapi.testclient import TestClient
import pytest

from src.app import app

client = TestClient(app)


def get_participants(activity_name: str):
    resp = client.get("/activities")
    assert resp.status_code == 200
    activities = resp.json()
    assert activity_name in activities
    return activities[activity_name].get("participants", [])


def ensure_removed(activity_name: str, email: str):
    # attempt to delete; ignore not found
    resp = client.delete(f"/activities/{activity_name}/participants", params={"email": email})
    return resp


def test_get_activities_contains_known_activity():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "pytest-user@example.com"

    # Ensure clean start (remove if already present)
    ensure_removed(activity, email)

    # Signup
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Participant appears in GET
    participants = get_participants(activity)
    assert email in participants

    # Unregister
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # No longer present
    participants = get_participants(activity)
    assert email not in participants


def test_signup_existing_returns_400():
    activity = "Programming Class"
    email = "existing-check@example.com"

    # Ensure removed, then add
    ensure_removed(activity, email)
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200

    # Second signup should fail
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 400

    # Cleanup
    ensure_removed(activity, email)


def test_unregister_nonexistent_returns_404():
    activity = "Art Club"
    email = "not-present@example.com"

    # Ensure not present
    ensure_removed(activity, email)

    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp.status_code == 404


def test_activity_not_found_returns_404_on_signup():
    resp = client.post("/activities/NoSuchActivity/signup", params={"email": "x@example.com"})
    assert resp.status_code == 404
