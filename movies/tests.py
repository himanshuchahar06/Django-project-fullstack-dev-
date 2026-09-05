import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from movies.models import Movie, Theater, Seat, Booking, PaymentTransaction

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

    def test_create_payment_order_and_verify_success(self):
        """Test complete payment order creation and server-side verification."""
        # Step 1: Reserve seat A1
        self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )

        # Step 2: Create payment order
        res_order = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/payment/create-order/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.assertEqual(res_order.status_code, 200)
        order_data = res_order.json()
        self.assertTrue(order_data['success'])
        order_id = order_data['order_id']
        self.assertEqual(order_data['amount'], 300.0)

        # Verify PaymentTransaction in database
        txn = PaymentTransaction.objects.get(order_id=order_id)
        self.assertEqual(txn.status, 'PENDING')
        self.assertEqual(txn.user, self.user1)

        # Step 3: Verify payment server-side
        res_verify = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/payment/verify/',
            data=json.dumps({
                'order_id': order_id,
                'payment_id': 'pay_test123',
                'signature': 'sandbox_signature_verified'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_verify.status_code, 200)
        self.assertTrue(res_verify.json()['success'])

        # Verify database state
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'SUCCESS')
        self.assertEqual(txn.payment_id, 'pay_test123')

        self.seat1.refresh_from_db()
        self.assertTrue(self.seat1.is_booked)
        self.assertTrue(Booking.objects.filter(user=self.user1, seat=self.seat1, payment=txn).exists())

    def test_duplicate_payment_verification_idempotency(self):
        """Test that sending duplicate payment verification requests never creates duplicate bookings."""
        # Setup reserved seat and payment transaction
        self.seat1.reserved_by = self.user1
        self.seat1.reserved_until = timezone.now() + timedelta(minutes=2)
        self.seat1.save()

        txn = PaymentTransaction.objects.create(
            user=self.user1,
            order_id='order_idem_123',
            amount=300.0,
            currency='INR',
            status='PENDING',
            movie=self.movie,
            theater=self.theater,
            seats_summary='A1'
        )

        url = f'/movies/theater/{self.theater.id}/payment/verify/'
        payload = json.dumps({
            'order_id': 'order_idem_123',
            'payment_id': 'pay_idem_456',
            'signature': 'sandbox_signature_verified'
        })

        # Request 1: First payment verification
        res1 = self.client_user1.post(url, data=payload, content_type='application/json')
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json()['success'])
        booking_count_initial = Booking.objects.filter(user=self.user1, seat=self.seat1).count()
        self.assertEqual(booking_count_initial, 1)

        # Request 2: Duplicate payment verification retry
        res2 = self.client_user1.post(url, data=payload, content_type='application/json')
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json()['already_processed'])

        # Verify duplicate booking was NOT created
        booking_count_final = Booking.objects.filter(user=self.user1, seat=self.seat1).count()
        self.assertEqual(booking_count_final, 1)

    def test_failed_payment_releases_reserved_seats(self):
        """Test that payment failure automatically releases reserved seats back to available."""
        # Reserve seat A1
        self.client_user1.post(
            f'/movies/theater/{self.theater.id}/reserve-seats/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        self.seat1.refresh_from_db()
        self.assertEqual(self.seat1.reserved_by, self.user1)

        # Create order
        res_order = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/payment/create-order/',
            data=json.dumps({'seat_ids': [self.seat1.id]}),
            content_type='application/json'
        )
        order_id = res_order.json()['order_id']

        # Handle failure
        res_fail = self.client_user1.post(
            f'/movies/theater/{self.theater.id}/payment/failure/',
            data=json.dumps({'order_id': order_id, 'reason': 'Payment cancelled by user.'}),
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 200)
        self.assertTrue(res_fail.json()['released'])

        # Verify seat A1 is released and transaction marked CANCELLED
        self.seat1.refresh_from_db()
        self.assertIsNone(self.seat1.reserved_by)
        self.assertFalse(self.seat1.is_booked)

        txn = PaymentTransaction.objects.get(order_id=order_id)
        self.assertEqual(txn.status, 'CANCELLED')
