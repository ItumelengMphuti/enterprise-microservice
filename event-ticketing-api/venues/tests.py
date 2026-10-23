
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Venue, Seat


class SeatConstraintTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            address="1 Test Street",
            city="Johannesburg",
        )

    def test_seat_location_must_be_unique_within_venue(self):
        Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Seat.objects.create(
                    venue=self.venue,
                    row_label="A",
                    seat_number=1,
                )

    def test_same_seat_number_is_allowed_in_another_venue(self):
        another_venue = Venue.objects.create(
            name="Second Arena",
            address="2 Test Street",
            city="Pretoria",
        )

        Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )

        another_seat = Seat.objects.create(
            venue=another_venue,
            row_label="A",
            seat_number=1,
        )

        self.assertEqual(another_seat.seat_number, 1)

