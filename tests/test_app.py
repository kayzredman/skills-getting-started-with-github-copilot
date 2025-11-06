from fastapi.testclient import TestClient
from copy import deepcopy
from urllib.parse import quote
import pytest

from src.app import app, activities


client = TestClient(app)


# Keep a pristine copy of the initial activities so tests can restore state
_ORIG_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities before each test to avoid cross-test pollution."""
    activities.clear()
    activities.update(deepcopy(_ORIG_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(_ORIG_ACTIVITIES))


def test_get_activities_returns_dictionary():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect at least one known activity from the sample data
    assert "Chess Club" in data


def test_signup_duplicate_and_unregister_flow():
    activity = "Chess Club"
    email = "tester@example.com"

    # Ensure email is not already present
    assert email not in activities[activity]["participants"]

    # Sign up the user
    resp = client.post(f"/activities/{quote(activity, safe='')}/signup", params={"email": email})
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")
    assert email in activities[activity]["participants"]

    # Duplicate signup should return 400
    resp_dup = client.post(f"/activities/{quote(activity, safe='')}/signup", params={"email": email})
    assert resp_dup.status_code == 400

    # Now unregister the user
    resp_un = client.delete(f"/activities/{quote(activity, safe='')}/unregister", params={"email": email})
    assert resp_un.status_code == 200
    body_un = resp_un.json()
    assert "Unregistered" in body_un.get("message", "")
    assert email not in activities[activity]["participants"]
