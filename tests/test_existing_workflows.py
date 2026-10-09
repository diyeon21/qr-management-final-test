from app import app as flask_app


def _set_session(client, role):
    with client.session_transaction() as session:
        session["user"] = {
            "id": "1",
            "name": f"{role.title()} User",
            "email": f"{role}@example.com",
            "role": role,
        }
        session["last_activity"] = "9999999999"


def test_admin_has_full_control():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "admin")
        assert client.get("/dashboard/admin").status_code == 200
        assert client.get("/admin_reports/").status_code == 200
        assert client.get("/user_management/").status_code == 200
        assert client.get("/equipment/").status_code == 200
        assert client.get("/maintenance_requests/").status_code == 200
        assert client.get("/logbook/").status_code == 200
        assert client.get("/scan").status_code == 200


def test_custodian_stocks_and_inventory_access():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "custodian")
        assert client.get("/dashboard/custodian").status_code == 200
        assert client.get("/equipment/").status_code == 200
        assert client.get("/scan").status_code == 200
        # Custodian restricted from maintenance requests and user management
        assert client.get("/maintenance_requests/").status_code == 403
        assert client.get("/user_management/").status_code == 403
        assert client.get("/admin_reports/").status_code == 403


def test_technician_repair_maintenance_inventory_access():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "technician")
        assert client.get("/dashboard/technician").status_code == 200
        assert client.get("/maintenance_requests/").status_code == 200
        assert client.get("/logbook/").status_code == 200
        assert client.get("/equipment/").status_code == 200
        assert client.get("/scan").status_code == 200
        # Technician restricted from admin-only sections
        assert client.get("/user_management/").status_code == 403
        assert client.get("/admin_reports/").status_code == 403


def test_faculty_dashboard_manual_report_and_scan_work():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _set_session(client, "faculty")
        assert client.get("/dashboard/faculty").status_code == 200
        assert client.get("/admin_reports/manual_report").status_code == 200
        assert client.get("/scan").status_code == 200
        assert client.get("/my_requests/").status_code == 200
        # Faculty restricted from custodian/technician/admin management
        assert client.get("/equipment/").status_code == 403
        assert client.get("/maintenance_requests/").status_code == 403
        assert client.get("/logbook/").status_code == 403
