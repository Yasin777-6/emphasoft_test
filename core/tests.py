# core/tests.py
import threading
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase

from rest_framework import status
from rest_framework.test import APIClient

from .models import Room, Booking

REGISTER_URL = "/api/auth/register/"
TOKEN_URL = "/api/auth/token/"

ROOMS_URL = "/api/rooms/"
AVAILABLE_ROOMS_URL = "/api/rooms/available/"

BOOKING_CREATE_URL = "/api/booking/create"
MY_BOOKINGS_URL = "/api/booking/list/me"
CANCEL_URL_TMPL = "/api/booking/cancel/{pk}"


def _unwrap_list_response(data):
rns a plain list.
    
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class HotelBookingAPITests(TestCase):
    

    def setUp(self) -> None:
        self.client = APIClient()
        self.anon = APIClient()

        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.superuser = User.objects.create_superuser(username="admin", password="adminpassword")

        self.room = Room.objects.create(name="Room 101", capacity=2, cost_per_day="100.00")

        # Authenticate testuser
        token_resp = self.client.post(TOKEN_URL, {"username": "testuser", "password": "testpassword"}, format="json")
        self.assertEqual(token_resp.status_code, status.HTTP_200_OK, token_resp.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_resp.data['access']}")

    def test_register_user(self):
        resp = self.anon.post(REGISTER_URL, {"username": "newuser", "password": "newpassword"}, format="json")
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED), resp.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_get_rooms_anonymous(self):
        resp = self.anon.get(ROOMS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        items = _unwrap_list_response(resp.data)
        self.assertEqual(len(items), 1)

    def test_create_booking_success(self):
        today = date.today()
        payload = {
            "room": self.room.id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=2)).isoformat(),
        }
        resp = self.client.post(BOOKING_CREATE_URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(Booking.objects.count(), 1)

    def test_create_booking_rejects_overlap(self):
        today = date.today()
        Booking.objects.create(
            user=self.user,
            room=self.room,
            start_date=today,
            end_date=today + timedelta(days=2),
            is_canceled=False,
        )

        payload = {
            "room": self.room.id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=2)).isoformat(),
        }
        resp = self.client.post(BOOKING_CREATE_URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.data)

    def test_cancel_booking_owner(self):
        today = date.today()
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            start_date=today,
            end_date=today + timedelta(days=2),
            is_canceled=False,
        )

        resp = self.client.post(CANCEL_URL_TMPL.format(pk=booking.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        booking.refresh_from_db()
        self.assertTrue(booking.is_canceled)

    def test_cancel_booking_superuser(self):
        today = date.today()
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            start_date=today,
            end_date=today + timedelta(days=2),
            is_canceled=False,
        )

        admin_client = APIClient()
        token_resp = admin_client.post(TOKEN_URL, {"username": "admin", "password": "adminpassword"}, format="json")
        self.assertEqual(token_resp.status_code, status.HTTP_200_OK, token_resp.data)
        admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_resp.data['access']}")

        resp = admin_client.post(CANCEL_URL_TMPL.format(pk=booking.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        booking.refresh_from_db()
        self.assertTrue(booking.is_canceled)

    def test_available_rooms_excludes_active_overlapping_booking(self):
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=2)

        
        resp1 = self.anon.get(
            f"{AVAILABLE_ROOMS_URL}?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK, resp1.data)
        items1 = _unwrap_list_response(resp1.data)
        self.assertEqual(len(items1), 1)

    
        Booking.objects.create(
            user=self.user,
            room=self.room,
            start_date=start_date,
            end_date=end_date,
            is_canceled=False,
        )

        resp2 = self.anon.get(
            f"{AVAILABLE_ROOMS_URL}?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK, resp2.data)
        items2 = _unwrap_list_response(resp2.data)
        self.assertEqual(len(items2), 0)

    def test_available_rooms_ignores_canceled_booking(self):
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=2)

        Booking.objects.create(
            user=self.user,
            room=self.room,
            start_date=start_date,
            end_date=end_date,
            is_canceled=True, 
        )

        resp = self.anon.get(
            f"{AVAILABLE_ROOMS_URL}?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        items = _unwrap_list_response(resp.data)
        self.assertEqual(len(items), 1)

    def test_n_plus_one_my_bookings_list(self):
    
        today = date.today()

        for i in range(10):
            r = Room.objects.create(name=f"Room {200+i}", capacity=2, cost_per_day="99.00")
            Booking.objects.create(
                user=self.user,
                room=r,
                start_date=today,
                end_date=today + timedelta(days=1),
                is_canceled=False,
            )

        with self.assertNumQueries(2):
            resp = self.client.get(MY_BOOKINGS_URL)
            self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)


class HotelBookingAtomicTests(TransactionTestCase):
 
    reset_sequences = True

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(username="u1", password="pass12345")
        self.user2 = User.objects.create_user(username="u2", password="pass12345")
        self.room = Room.objects.create(name="Room Atomic", capacity=2, cost_per_day="120.00")

        today = date.today()
        self.payload = {
            "room": self.room.id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=2)).isoformat(),
        }

    def _token_for(self, username: str, password: str) -> str:
        c = APIClient()
        resp = c.post(TOKEN_URL, {"username": username, "password": password}, format="json")
        assert resp.status_code == 200, resp.data
        return resp.data["access"]

    def _book_in_thread(self, token: str, results: list, idx: int) -> None:
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = c.post(BOOKING_CREATE_URL, self.payload, format="json")
        results[idx] = resp.status_code

    def test_atomic_double_booking_same_room_same_dates(self):
        if connection.vendor == "sqlite":
            self.skipTest("Row-lock concurrency test is unreliable on SQLite. Run on PostgreSQL.")

        token1 = self._token_for("u1", "pass12345")
        token2 = self._token_for("u2", "pass12345")

        results = [None, None]

        t1 = threading.Thread(target=self._book_in_thread, args=(token1, results, 0))
        t2 = threading.Thread(target=self._book_in_thread, args=(token2, results, 1))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        
        self.assertEqual(Booking.objects.filter(room=self.room, is_canceled=False).count(), 1)

        
        self.assertIn(status.HTTP_201_CREATED, results)
        self.assertTrue(
            any(code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT) for code in results),
            msg=f"Expected one 201 and one 400/409, got {results}",
        )
