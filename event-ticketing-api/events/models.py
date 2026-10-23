from django.core.exceptions import ValidationError
from django.db import models


class Event(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    venue = models.ForeignKey(
        "venues.Venue",
        on_delete=models.PROTECT,
        related_name="events",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(
                fields=["start_time"],
                name="event_start_time_idx",
            )
        ]

    def __str__(self):
        return self.title



class EventSeat(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_seats",
    )
    seat = models.ForeignKey(
        "venues.Seat",
        on_delete=models.PROTECT,
        related_name="event_offerings",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def clean(self):
        super().clean()

        if self.event_id and self.seat_id:
            if self.event.venue_id != self.seat.venue_id:
                raise ValidationError({
                    "seat": "The seat must belong to the event's venue."
                })

        if self.price is not None and self.price < 0:
            raise ValidationError({
                "price": "Ticket price cannot be negative."
            })

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "seat"],
                name="uniq_event_seat",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="event_seat_price_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.seat}"

