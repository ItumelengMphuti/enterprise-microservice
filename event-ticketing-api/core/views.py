
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


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
            },
            status=200,
        )

    except Exception:
        return JsonResponse(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": timezone.now().isoformat(),
            },
            status=503,
        )
