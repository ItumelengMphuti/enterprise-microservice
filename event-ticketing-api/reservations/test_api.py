from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from venues.models import Venue, Seat
from events.models import Event, EventSeat
from reservations.models import Reservation


User = get_user_model()


class ReservationAPITests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer_api",
            password="TestPassword123!",
        )
        self.other_customer = User.objects.create_user(
            username="other_customer_api",
            password="TestPassword456!",
        )

        self.venue = Venue.objects.create(
            name="API Test Arena",
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
            title="API Test Concert",
            start_time=timezone.now(),
        )
        self.event_seat = EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )

        self.reservation_url = "/api/reservations/"

    def create_reservation(self, user):
        return Reservation.objects.create(
            user=user,
            event_seat=self.event_seat,
            status=Reservation.Status.CONFIRMED,
        )

    def test_reservations_require_authentication(self):
        response = self.client.get(self.reservation_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_only_sees_their_own_reservations(self):
        own_reservation = self.create_reservation(self.customer)

        # Create a different seat for the other customer's reservation.
        another_seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=2,
        )
        another_event_seat = EventSeat.objects.create(
            event=self.event,
            seat=another_seat,
            price=Decimal("350.00"),
        )
        Reservation.objects.create(
            user=self.other_customer,
            event_seat=another_event_seat,
            status=Reservation.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.reservation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data]

        self.assertEqual(returned_ids, [own_reservation.id])


    def test_customer_cannot_view_another_customers_reservation(self):
        other_reservation = self.create_reservation(self.other_customer)

        self.client.force_authenticate(user=self.customer)

        response = self.client.get(
            f"{self.reservation_url}{other_reservation.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cannot_directly_update_reservation(self):
        reservation = self.create_reservation(self.customer)
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            f"{self.reservation_url}{reservation.id}/",
            {"status": "CANCELLED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_delete_reservation(self):
        reservation = self.create_reservation(self.customer)
        self.client.force_authenticate(user=self.customer)

        response = self.client.delete(
            f"{self.reservation_url}{reservation.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_create_reservation_for_themselves(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.reservation_url,
            {
                "user": self.other_customer.id,
                "event_seat": self.event_seat.id,
                "status": "CONFIRMED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=response.data["id"])

        self.assertEqual(reservation.user, self.customer)
        self.assertEqual(reservation.status, Reservation.Status.PENDING)
        
        
    def test_customer_cannot_book_an_already_reserved_seat(self):
        self.create_reservation(self.other_customer)
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.reservation_url,
            {"event_seat": self.event_seat.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("event_seat", response.data)

