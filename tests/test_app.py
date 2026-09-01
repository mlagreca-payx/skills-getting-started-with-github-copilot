from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


initial_activities = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(initial_activities))


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_activity = initial_activities["Chess Club"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity = "Chess Club"
    email = "new.student+test@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity}"
    }
    assert email in app_module.activities[activity]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = initial_activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    # Arrange
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant(client):
    # Arrange
    activity = "Chess Club"
    email = initial_activities[activity]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity}"
    }
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_rejects_unknown_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_participant_can_register_again_after_unregistering(client):
    # Arrange
    activity = "Chess Club"
    email = initial_activities[activity]["participants"][0]

    # Act
    delete_response = client.delete(f"/activities/{activity}/participants/{email}")
    signup_response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert delete_response.status_code == 200
    assert signup_response.status_code == 200
    assert email in app_module.activities[activity]["participants"]