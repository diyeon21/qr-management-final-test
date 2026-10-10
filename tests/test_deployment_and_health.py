import json
import unittest
from app import app as flask_app
import config

class TestDeploymentAndHealth(unittest.TestCase):
    def setUp(self):
        flask_app.config.update(TESTING=True)
        self.client = flask_app.test_client()

    def test_health_check_endpoint(self):
        """Verify the health check endpoint returns 200 OK and connected database."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("database"), "connected")
        self.assertIn("version", data)

    def test_security_headers_present(self):
        """Verify essential security headers are applied to responses."""
        response = self.client.get("/auth/login")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("no-cache", response.headers.get("Cache-Control", ""))

    def test_uploads_folder_configured(self):
        """Verify uploads folder is configured and exists."""
        import os
        self.assertTrue(os.path.exists(config.UPLOAD_FOLDER))
