
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from venues.models import Venue, Seat
from .models import Event, EventSeat
from .serializers import EventSeatSerializer


User = get_user_model()


class EventSeatConstraintTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )
        self.event = Event.objects.create(
            venue=self.venue,
            title="Test Concert",
            start_time=timezone.now(),
        )

    def test_same_seat_cannot_be_added_twice_to_event(self):
        EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )
        self.assertTrue(self.event.seats.filter(pk=self.seat.pk).exists())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventSeat.objects.create(
                    event=self.event,
                    seat=self.seat,
                    price=Decimal("350.00"),
                )

    def test_negative_ticket_price_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventSeat.objects.create(
                    event=self.event,
                    seat=self.seat,
                    price=Decimal("-10.00"),
                )

    def test_seat_must_belong_to_event_venue(self):
        other_venue = Venue.objects.create(
            name="Other Arena",
            address="2 Test Street",
            city="Pretoria",
        )
        other_seat = Seat.objects.create(
            venue=other_venue,
            row_label="B",
            seat_number=1,
        )

        offering = EventSeat(
            event=self.event,
            seat=other_seat,
            price=Decimal("200.00"),
        )

        with self.assertRaises(ValidationError):
            offering.full_clean()


class EventSeatSerializerTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Serializer Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.other_venue = Venue.objects.create(
            name="Other Arena",
            address="2 Test Street",
            city="Pretoria",
        )
        self.seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )
        self.second_seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=2,
        )
        self.other_seat = Seat.objects.create(
            venue=self.other_venue,
            row_label="A",
            seat_number=1,
        )
        self.event = Event.objects.create(
            venue=self.venue,
            title="Serializer Concert",
            start_time=timezone.now(),
        )
        self.offering = EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )

    def test_valid_event_seat_is_accepted(self):
        serializer = EventSeatSerializer(
            data={
                "event": self.event.pk,
                "seat": self.second_seat.pk,
                "price": "250.00",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_seat_from_another_venue_is_rejected(self):
        serializer = EventSeatSerializer(
            data={
                "event": self.event.pk,
                "seat": self.other_seat.pk,
                "price": "250.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("seat", serializer.errors)

    def test_negative_price_is_rejected(self):
        serializer = EventSeatSerializer(
            data={
                "event": self.event.pk,
                "seat": self.second_seat.pk,
                "price": "-1.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_partial_update_uses_values_from_existing_offering(self):
        serializer = EventSeatSerializer(
            self.offering,
            data={"price": "400.00"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class EventAPITests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="event_staff",
            password="test-password",
            is_staff=True,
        )
        self.venue = Venue.objects.create(
            name="API Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.event = Event.objects.create(
            venue=self.venue,
            title="API Concert",
            start_time=timezone.now(),
        )

    def test_events_can_be_listed_and_retrieved_without_authentication(self):
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"/api/events/{self.event.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "API Concert")

    def test_staff_can_create_update_and_delete_events(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            "/api/events/",
            {
                "venue": self.venue.pk,
                "title": "New Concert",
                "start_time": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        event_id = response.data["id"]

        response = self.client.patch(
            f"/api/events/{event_id}/",
            {"title": "Updated Concert"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Concert")

        response = self.client.delete(f"/api/events/{event_id}/")
        self.assertEqual(response.status_code, 204)

    def test_non_staff_cannot_create_events(self):
        user = User.objects.create_user(
            username="event_customer",
            password="test-password",
        )
        self.client.force_authenticate(user)

        response = self.client.post(
            "/api/events/",
            {
                "venue": self.venue.pk,
                "title": "Forbidden Concert",
                "start_time": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.data)


class EventSeatAPITests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="event_seat_staff",
            password="test-password",
            is_staff=True,
        )
        self.venue = Venue.objects.create(
            name="Event Seat Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )
        self.event = Event.objects.create(
            venue=self.venue,
            title="Event Seat Concert",
            start_time=timezone.now(),
        )
        self.offering = EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )

    def test_event_seats_can_be_listed_and_retrieved_publicly(self):
        response = self.client.get("/api/event-seats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            f"/api/event-seats/{self.offering.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["event"], self.event.pk)

    def test_staff_can_create_update_and_delete_event_seats(self):
        self.client.force_authenticate(self.staff)
        second_seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=2,
        )
        response = self.client.post(
            "/api/event-seats/",
            {
                "event": self.event.pk,
                "seat": second_seat.pk,
                "price": "250.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        offering_id = response.data["id"]

        response = self.client.patch(
            f"/api/event-seats/{offering_id}/",
            {"price": "275.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "275.00")

        response = self.client.delete(f"/api/event-seats/{offering_id}/")
        self.assertEqual(response.status_code, 204)

    def test_event_seat_validation_uses_standard_error_response(self):
        other_venue = Venue.objects.create(
            name="Different Arena",
            address="2 Test Street",
            city="Pretoria",
        )
        other_seat = Seat.objects.create(
            venue=other_venue,
            row_label="A",
            seat_number=1,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            "/api/event-seats/",
            {
                "event": self.event.pk,
                "seat": other_seat.pk,
                "price": "250.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "invalid",
        )
        self.assertIn("seat", response.data["error"]["details"])
