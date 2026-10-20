
from django.conf import settings
from django.db import models


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    event_seat = models.ForeignKey(
        "events.EventSeat",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reserved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reserved_at"]
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="reservation_user_status_idx",
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event_seat"],
                condition=models.Q(
                    status__in=["PENDING", "CONFIRMED"]
                ),
                name="uniq_active_res_eventseat",
            )
        ]

    def __str__(self):
        return (
            f"{self.user} - {self.event_seat} "
            f"({self.status})"
        )
