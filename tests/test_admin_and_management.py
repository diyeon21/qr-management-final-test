from unittest.mock import patch
from app import app as flask_app
import routes.user_mgmt as user_mgmt_module
import routes.equipment as equipment_module
import routes.requests as requests_module


def _set_session(client, role="admin", user_id=1):
    with client.session_transaction() as session:
        session["user"] = {
            "id": user_id,
            "name": f"{role.title()} User",
            "email": f"{role}@neust.edu.ph",
            "role": role,
        }
        session["last_activity"] = "9999999999"
        session["_csrf_token"] = "valid-token-for-test-xyz"


def test_admin_cannot_delete_own_account():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "admin", user_id=1)
        response = client.post(
            "/user_management/delete/1",
            data={"csrf_token": "valid-token-for-test-xyz"},
            follow_redirects=True
        )
        assert response.status_code == 200
        # Should redirect back to user management with flash warning


def test_equipment_delete_endpoint_requires_csrf():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "admin", user_id=1)
        # Without CSRF token, should fail with 400
        response = client.post("/equipment/delete/99")
        assert response.status_code == 400


def test_request_status_update_resolved_requires_action():
    class FakeCursor:
        def execute(self, *args, **kwargs):
            return None
        def fetchone(self):
            return {"equipment_id": 1, "reported_by": 2, "equipment_name": "PC 01"}
        def close(self):
            return None

    class FakeDB:
        def cursor(self, dictionary=True):
            return FakeCursor()
        def commit(self):
            return None
        def close(self):
            return None

    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "technician", user_id=3)
        with patch.object(requests_module, "get_db", return_value=FakeDB()):
            response = client.post(
                "/maintenance_requests/",
                data={
                    "csrf_token": "valid-token-for-test-xyz",
                    "request_id": "10",
                    "status": "Resolved",
                    "action_taken": "",
                },
                follow_redirects=False
            )
            assert response.status_code == 302
            assert "error=action_required" in response.headers["Location"]


def test_notifications_unread_api():
    class FakeCursor:
        def execute(self, *args, **kwargs):
            return None
        def fetchone(self):
            return {"c": 3}
        def fetchall(self):
            return [
                {"id": 1, "message": "Test notif 1", "link": "/my_requests", "is_read": 0, "created_at": None},
                {"id": 2, "message": "Test notif 2", "link": "/my_requests", "is_read": 0, "created_at": None},
            ]
        def close(self):
            return None

    class FakeDB:
        def cursor(self, dictionary=True):
            return FakeCursor()
        def close(self):
            return None

    import routes.notifications as notif_module

    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        # Unauthenticated returns empty count 0
        resp = client.get("/notifications/api/unread")
        assert resp.status_code == 200
        assert resp.json["count"] == 0

        # Authenticated returns notifications list
        _set_session(client, "faculty", user_id=9)
        with patch.object(notif_module, "get_db", return_value=FakeDB()):
            resp = client.get("/notifications/api/unread")
            assert resp.status_code == 200
            assert resp.json["count"] == 3
            assert len(resp.json["notifications"]) == 2


def test_equipment_soft_delete_flow():
    deleted_queries = []

    class FakeCursor:
        def execute(self, sql, params=None):
            deleted_queries.append((sql, params))
        def fetchone(self):
            return {"id": 15, "name": "Lab 1 PC 05"}
        def close(self):
            return None

    class FakeDB:
        def cursor(self, dictionary=True):
            return FakeCursor()
        def commit(self):
            return None
        def close(self):
            return None

    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "admin", user_id=1)
        with patch.object(equipment_module, "get_db", return_value=FakeDB()):
            response = client.post(
                "/equipment/delete/15",
                data={"csrf_token": "valid-token-for-test-xyz"},
                follow_redirects=False
            )
            assert response.status_code == 302
            assert response.headers["Location"].endswith("/equipment/")
            assert any("is_deleted=1" in q[0] for q in deleted_queries)
