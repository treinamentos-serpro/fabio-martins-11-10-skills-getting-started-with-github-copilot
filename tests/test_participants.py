import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from src.app import activities, app


class ParticipantTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)
        self.url = "/activities/Chess%20Club/participants"
        self.email = "michael@mergington.edu"

    def tearDown(self):
        activities.clear()
        activities.update(self.original_activities)
        self.client.close()

    def test_unregister_removes_only_selected_participant(self):
        before = activities["Chess Club"]["participants"][:]
        response = self.client.delete(self.url, params={"email": self.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": f"Unregistered {self.email} from Chess Club"
        })
        expected = [email for email in before if email != self.email]
        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"],
            expected,
        )
        self.assertEqual(
            activities["Programming Class"],
            self.original_activities["Programming Class"],
        )

    def test_missing_activity(self):
        response = self.client.delete(
            "/activities/Unknown/participants", params={"email": self.email}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(activities, self.original_activities)

    def test_missing_participant_and_repeated_removal(self):
        self.client.delete(self.url, params={"email": self.email})
        after_removal = deepcopy(activities)
        response = self.client.delete(self.url, params={"email": self.email})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"], "Student is not signed up for this activity"
        )
        self.assertEqual(activities, after_removal)

    def test_email_is_required(self):
        self.assertEqual(self.client.delete(self.url).status_code, 422)
        self.assertEqual(activities, self.original_activities)

    def test_signup_then_remove_last_participant(self):
        params = {"email": "new+student@mergington.edu"}
        self.assertEqual(
            self.client.post("/activities/Art%20Club/signup", params=params).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(
                "/activities/Art%20Club/participants", params=params
            ).status_code,
            200,
        )
        self.assertEqual(activities["Art Club"]["participants"], [])


if __name__ == "__main__":
    unittest.main()
