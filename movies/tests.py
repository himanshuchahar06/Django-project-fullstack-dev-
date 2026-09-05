import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from movies.models import Movie, Theater, Seat, Booking

class SmartSeatReservationTestCase(TestCase):
    def setUp(self):
        self.client_user1 = Client()
        self.client_user2 = Client()

        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        self.client_user1.login(username='alice', password='password123')
        self.client_user2.login(username='bob', password='password123')

        self.movie = Movie.objects.create(
            name='Test Inception',
            rating=9.5,
            duration_minutes=148,
            age_certification='UA'
        )

        self.theater = Theater.objects.create(
            name='IMAX Screen 1',
            location='Central Mall',
            movie=self.movie,
            time=timezone.now() + timedelta(days=1),
            ticket_price=300.00
        )

        self.seat1 = Seat.objects.create(theater=self.theater, seat_number='A1')
        self.seat2 = Seat.objects.create(theater=self.theater, seat_number='A2')
        self.seat3 = Seat.objects.create(theater=self.theater, seat_number='A3')

    def test_seat_reservation_success_and_2min_lock(self):
        """User 1 reserves Seat A1; check 2-min lock and status for User 1 vs User 2."""
        url = f'/movies/theater/{self.theater.id}/reserve-seats/'
        response = self.client_user1.post(
            url,
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['remaining_seconds'], 120)

        # Check status from User 1's perspective
        status_url = f'/movies/theater/{self.theater.id}/seat-status/'
        res_u1 = self.client_user1.get(status_url).json()
        s1_u1 = next(s for s in res_u1['seats'] if s['id'] == self.seat1.id)
        self.assertEqual(s1_u1['status'], 'reserved_by_you')

        # Check status from User 2's perspective
        res_u2 = self.client_user2.get(status_url).json()
        s1_u2 = next(s for s in res_u2['seats'] if s['id'] == self.seat1.id)
        self.assertEqual(s1_u2['status'], 'reserved_by_other')

    def test_concurrent_reservation_conflict(self):
        """User 1 reserves Seat A1; User 2 attempts to reserve Seat A1 and is blocked with 409 conflict."""
        # User 1 reserves A1
        self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )

        # User 2 attempts to reserve A1
        response = self.client_user2.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("reserved by another user", data['error'])

    def test_auto_release_after_2_minutes(self):
        """Expired reservations (> 120 seconds) automatically revert to available."""
        self.seat1.reserved_by = self.user1
        self.seat1.reserved_until = timezone.now() - timedelta(seconds=10) # Expired
        self.seat1.save()

        # User 2 checks status or reserves seat
        status_url = f'/movies/theater/{self.theater.id}/seat-status/'
        res = self.client_user2.get(status_url).json()
        s1 = next(s for s in res['seats'] if s['id'] == self.seat1.id)
        self.assertEqual(s1['status'], 'available')

        # User 2 can now reserve A1 successfully
        res_reserve = self.client_user2.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.assertEqual(res_reserve.status_code, 200)
        self.assertTrue(res_reserve.json()['success'])

    def test_modify_seat_selection_before_payment(self):
        """User 1 reserves A1, then modifies selection to A2 & A3."""
        # Step 1: Reserve A1
        self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )

        # Step 2: Modify reservation to A2 & A3
        res = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat2.id, self.seat3.id]}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)

        # Verify A1 is released and A2, A3 are reserved by User 1
        self.seat1.refresh_from_db()
        self.seat2.refresh_from_db()
        self.seat3.refresh_from_db()

        self.assertIsNone(self.seat1.reserved_by)
        self.assertEqual(self.seat2.reserved_by, self.user1)
        self.assertEqual(self.seat3.reserved_by, self.user1)

    def test_confirm_booking_success(self):
        """User 1 reserves A1 and confirms booking, turning seat to booked status."""
        self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )

        # Confirm booking
        res = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/confirm-booking/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['success'])

        self.seat1.refresh_from_db()
        self.assertTrue(self.seat1.is_booked)
        self.assertIsNone(self.seat1.reserved_by)
        self.assertTrue(Booking.objects.filter(user=self.user1, seat=self.seat1).exists())
