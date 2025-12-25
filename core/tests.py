from django.test import TestCase
from rest_framework.test import APITestCase
from .models import Room

class BookingAuthTests(APITestCase):
    def test_booking_create(self):
        room = Room.objects.create(
            name='101',
            capacity=5,
            cost_per_day=1000,
        )

        url='/api/booking/create'
        payload = {
            'room': room.id,
            'start_date':'2026-01-10',
            'end_date':'2026-01-14'
        }

        response = self.client.post(url,payload,format='json')

        self.assertEqual(response.status_code, 401)
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from .models import Room, Booking


class BookingMyListTests(APITestCase):
    def test_my_bookings_returns_only_authenticated_user_bookings(self):
    
        user1 = User.objects.create_user(username="user1", password="pass123")
        user2 = User.objects.create_user(username="user2", password="pass123")
        
        room = Room.objects.create(
            name="101",
            capacity=2,
            cost_per_day="100.00",
        )

    
        Booking.objects.create(
            user=user1,
            room=room,
            start_date="2026-01-10",
            end_date="2026-01-12",
        )

        Booking.objects.create(
            user=user2,
            room=room,
            start_date="2026-02-01",
            end_date="2026-02-03",
        )

    
        self.client.force_authenticate(user=user1)

    
        response = self.client.get("/api/booking/list/me")

    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        
