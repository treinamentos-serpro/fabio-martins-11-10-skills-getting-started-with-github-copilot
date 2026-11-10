from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def api_client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_activity_data(api_client):
    # Arrange
    expected_activities = deepcopy(activities)

    # Act
    response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert activities == expected_activities


def test_signup_adds_participant_once(api_client):
    # Arrange
    activity_name = "Art Club"
    email = "new+student@mergington.edu"
    original_participants = activities[activity_name]["participants"][:]

    # Act
    response = api_client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    participants = activities[activity_name]["participants"]
    assert participants.count(email) == 1
    assert [participant for participant in participants if participant != email] == (
        original_participants
    )


def test_signup_returns_404_for_missing_activity(api_client):
    # Arrange
    email = "new+student@mergington.edu"
    original_activities = deepcopy(activities)

    # Act
    response = api_client.post(
        "/activities/Unknown/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities == original_activities


def test_signup_returns_400_for_duplicate_participant(api_client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    original_activities = deepcopy(activities)

    # Act
    response = api_client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student already signed up for this activity"
    )
    assert activities == original_activities


def test_signup_requires_email(api_client):
    # Arrange
    original_activities = deepcopy(activities)

    # Act
    response = api_client.post("/activities/Art%20Club/signup")

    # Assert
    assert response.status_code == 422
    assert activities == original_activities