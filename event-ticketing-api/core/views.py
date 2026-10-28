
import logging
import time

from django.db import connection
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.utils import timezone


logger = logging.getLogger(__name__)
PROCESS_STARTED_AT = time.monotonic()


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": timezone.now().isoformat(),
                "uptime_seconds": round(
                    time.monotonic() - PROCESS_STARTED_AT,
                    2,
                ),
            },
            status=200,
        )

    except DatabaseError:
        logger.exception("Health check could not connect to the database")
        return JsonResponse(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": timezone.now().isoformat(),
                "uptime_seconds": round(
                    time.monotonic() - PROCESS_STARTED_AT,
                    2,
                ),
            },
            status=503,
        )
