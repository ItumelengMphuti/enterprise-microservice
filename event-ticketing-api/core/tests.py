
from django.db.utils import DatabaseError
from unittest.mock import patch

from django.test import TestCase


class HealthCheckTests(TestCase):
    def test_health_check_returns_healthy_when_database_is_connected(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["database"], "connected")
        self.assertIn("timestamp", response.json())
        self.assertGreaterEqual(response.json()["uptime_seconds"], 0)

        alias_response = self.client.get("/health/")
        self.assertEqual(alias_response.status_code, 200)
        self.assertEqual(alias_response.json()["status"], "healthy")

    @patch("core.views.connection.cursor")
    def test_health_check_returns_unhealthy_when_database_fails(
        self, mock_cursor
    ):
        mock_cursor.side_effect = DatabaseError("Database unavailable")

        with self.assertLogs("core.views", level="ERROR"):
            response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "unhealthy")
        self.assertEqual(response.json()["database"], "disconnected")
        self.assertIn("timestamp", response.json())
        self.assertGreaterEqual(response.json()["uptime_seconds"], 0)
