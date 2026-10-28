from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from .serializers import SeatSerializer
from .models import Venue, Seat


User = get_user_model()


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


class VenueAndSeatAPITests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="venue_staff",
            password="test-password",
            is_staff=True,
        )
        self.venue = Venue.objects.create(
            name="API Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )

    def test_venues_and_seats_can_be_listed_and_retrieved_publicly(self):
        response = self.client.get("/api/venues/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"/api/venues/{self.venue.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "API Arena")

        response = self.client.get("/api/seats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"/api/seats/{self.seat.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["row_label"], "A")

    def test_staff_can_create_update_and_delete_venues(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            "/api/venues/",
            {
                "name": "New Arena",
                "address": "2 Test Street",
                "city": "Pretoria",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        venue_id = response.data["id"]

        response = self.client.patch(
            f"/api/venues/{venue_id}/",
            {"city": "Cape Town"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["city"], "Cape Town")

        response = self.client.delete(f"/api/venues/{venue_id}/")
        self.assertEqual(response.status_code, 204)

    def test_staff_can_create_update_and_delete_seats(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            "/api/seats/",
            {
                "venue": self.venue.pk,
                "row_label": "B",
                "seat_number": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        seat_id = response.data["id"]

        response = self.client.patch(
            f"/api/seats/{seat_id}/",
            {"seat_number": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["seat_number"], 3)

        response = self.client.delete(f"/api/seats/{seat_id}/")
        self.assertEqual(response.status_code, 204)

    def test_non_staff_cannot_create_venues_or_seats(self):
        user = User.objects.create_user(
            username="venue_customer",
            password="test-password",
        )
        self.client.force_authenticate(user)

        venue_response = self.client.post(
            "/api/venues/",
            {
                "name": "Forbidden Arena",
                "address": "3 Test Street",
                "city": "Durban",
            },
            format="json",
        )
        self.assertEqual(venue_response.status_code, 403)
        self.assertIn("error", venue_response.data)

        seat_response = self.client.post(
            "/api/seats/",
            {
                "venue": self.venue.pk,
                "row_label": "C",
                "seat_number": 3,
            },
            format="json",
        )
        self.assertEqual(seat_response.status_code, 403)
        self.assertIn("error", seat_response.data)
