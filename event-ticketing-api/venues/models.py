from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Seat(models.Model):
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="seats",
    )
    row_label = models.CharField(max_length=10)
    seat_number = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["venue", "row_label", "seat_number"],
                name="uniq_seat_location",
            )
        ]
        ordering = ["row_label", "seat_number"]

    def __str__(self):
        return (
            f"{self.venue.name} - "
            f"Row {self.row_label}, Seat {self.seat_number}"
        )
