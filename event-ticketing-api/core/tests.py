
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_returns_healthy_when_database_is_connected(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["database"], "connected")
        self.assertIn("timestamp", response.json())

    @patch("core.views.connection.cursor")
    def test_health_check_returns_unhealthy_when_database_fails(
        self, mock_cursor
    ):
        mock_cursor.side_effect = Exception("Database unavailable")

        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "unhealthy")
        self.assertEqual(response.json()["database"], "disconnected")
        self.assertIn("timestamp", response.json())
