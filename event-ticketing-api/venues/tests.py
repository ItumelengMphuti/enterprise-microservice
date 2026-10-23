from django.db import IntegrityError, transaction
from django.test import TestCase
from .serializers import SeatSerializer
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


class SeatSerializerTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Serializer Test Arena",
            address="10 Test Street",
            city="Johannesburg",
        )

        Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )

    def test_duplicate_seat_location_is_rejected(self):
        serializer = SeatSerializer(
            data={
                "venue": self.venue.id,
                "row_label": "A",
                "seat_number": 1,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_unique_seat_location_is_valid(self):
        serializer = SeatSerializer(
            data={
                "venue": self.venue.id,
                "row_label": "A",
                "seat_number": 2,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_partial_update_uses_existing_seat_values(self):
        seat = Seat.objects.get(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )

        serializer = SeatSerializer(
            instance=seat,
            data={"seat_number": 2},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
