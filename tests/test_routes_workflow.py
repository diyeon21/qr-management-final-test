"""
Integration workflow verification testing routes with Flask test_client.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import get_db


class TestRoutesWorkflow(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        # Find or use an admin user from the database
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, name, email, role FROM users WHERE role = 'admin' LIMIT 1")
        self.admin_user = cur.fetchone()
        
        cur.execute("SELECT id, name, email, role FROM users WHERE role = 'technician' LIMIT 1")
        self.tech_user = cur.fetchone()

        cur.close()
        db.close()

    def test_admin_dashboard_loads(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        resp = self.client.get("/dashboard/admin")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Active Work Tracker", html)
        self.assertIn("Monthly Technician Metrics", html)
        self.assertIn("Problematic Hardware Watchlist", html)

    def test_equipment_management_laboratory_options(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        resp = self.client.get("/equipment/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        for i in range(1, 8):
            self.assertIn(f"Laboratory {i}", html)
        self.assertIn("Under Repair", html)
        self.assertIn("Not Working", html)

    def test_admin_reports_all_sections(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        resp = self.client.get("/admin_reports/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        
        # Check Section 3.0 (7-Lab Matrix)
        for i in range(1, 8):
            self.assertIn(f"Laboratory {i}", html)
        
        # Check Section 4.0 (Problem Identification)
        self.assertIn("Problem Identification &amp; Problematic Device Analytics", html)
        self.assertIn("Flagged Problematic Equipment Assets", html)
        
        # Check Section 5.0 (Technician Performance)
        self.assertIn("Technician Workload Monitoring &amp; Performance Reporting", html)

        # Check Section 6.0 (Recurring Incidents)
        self.assertIn("Recurring Incident Equipment", html)

        # Check Section 7.0 (Audit Trail with Calculated Duration)
        self.assertIn("Complete Maintenance &amp; Diagnostic Audit Trail", html)
        self.assertIn("Calculated Duration", html)
        self.assertIn("Start Date/Time", html)

    def test_admin_reports_individual_technician_dossier(self):
        if not self.tech_user:
            return
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        resp = self.client.get(f"/admin_reports/?technician_id={self.tech_user['id']}&time_window=90")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Dedicated Individual Technician Report Dossier", html)
        self.assertIn(self.tech_user["name"], html)

    def test_admin_reports_technician_csv_export(self):
        if not self.tech_user:
            return
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        resp = self.client.get(f"/admin_reports/?export=tech_csv&technician_id={self.tech_user['id']}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "text/csv")
        csv_data = resp.data.decode("utf-8")
        self.assertIn("Repair Duration", csv_data)
        self.assertIn("Repair Start Date", csv_data)
        self.assertIn("Completion Date", csv_data)

    def test_logbook_view_and_csv_export(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_user["id"]
            sess["user"] = self.admin_user
            sess["role"] = "admin"

        # View Logbook
        resp = self.client.get("/logbook/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Repair Timeline &amp; Duration", html)
        self.assertIn("Resolution &amp; Actions Taken", html)

        # Export CSV
        resp_csv = self.client.get("/logbook/?export=csv")
        self.assertEqual(resp_csv.status_code, 200)
        self.assertEqual(resp_csv.mimetype, "text/csv")
        csv_data = resp_csv.data.decode("utf-8")
        self.assertIn("Calculated Duration", csv_data)
        self.assertIn("Start Date/Time", csv_data)
        self.assertIn("Completion Date/Time", csv_data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
