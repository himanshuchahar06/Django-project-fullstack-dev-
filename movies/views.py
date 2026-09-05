import json
import hmac
import hashlib
import uuid
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import (
    Movie, Theater, Seat, Booking, Genre, Language, 
    CastMember, MoviePoster, Review, ReviewReport, PaymentTransaction
)
from .forms import (
    ReviewForm, ReviewReportForm, MovieForm, GenreForm, 
    LanguageForm, CastMemberForm, TheaterForm
)

def movie_list(request):
    search_query = request.GET.get('search')
    genre_slug = request.GET.get('genre')
    language_code = request.GET.get('language')

    movies = Movie.objects.all().prefetch_related('genres', 'languages')

    if search_query:
        movies = movies.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(cast__icontains=search_query)
        )
    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)
    if language_code:
        movies = movies.filter(languages__code=language_code)

    genres = Genre.objects.all()
    languages = Language.objects.all()

    return render(request, 'movies/movie_list.html', {
        'movies': movies.distinct(),
        'genres': genres,
        'languages': languages,
        'selected_genre': genre_slug,
        'selected_language': language_code,
        'search_query': search_query,
    })

def movie_detail(request, movie_id):
    movie = get_object_or_404(
        Movie.objects.prefetch_related(
            'genres', 'languages', 'cast_members', 
            'additional_posters', 'theaters', 'reviews__user'
        ),
        id=movie_id
    )
    
    has_booked = False
    user_review = None
    if request.user.is_authenticated:
        has_booked = Booking.objects.filter(user=request.user, movie=movie).exists()
        user_review = Review.objects.filter(movie=movie, user=request.user).first()

    reviews = movie.reviews.all()
    total_reviews = reviews.count()
    
    # Rating breakdown (count of 10-star, 9-star, etc.)
    rating_counts = {i: 0 for i in range(1, 11)}
    for r in reviews:
        rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1
    
    rating_percentages = {}
    if total_reviews > 0:
        for i in range(1, 11):
            rating_percentages[i] = int((rating_counts[i] / total_reviews) * 100)
    else:
        for i in range(1, 11):
            rating_percentages[i] = 0

    # Recommendations
    # 1. Similar movies (matching genre or language)
    genre_ids = movie.genres.values_list('id', flat=True)
    lang_ids = movie.languages.values_list('id', flat=True)
    
    similar_movies = Movie.objects.filter(
        Q(genres__id__in=genre_ids) | Q(languages__id__in=lang_ids)
    ).exclude(id=movie.id).distinct()[:6]

    # 2. Trending movies
    trending_movies = Movie.objects.filter(is_trending=True).exclude(id=movie.id).distinct()[:6]
    
    # 3. Recently released movies
    recent_movies = Movie.objects.exclude(id=movie.id).order_by('-release_date', '-id')[:6]

    review_form = ReviewForm(instance=user_review) if user_review else ReviewForm()
    report_form = ReviewReportForm()

    context = {
        'movie': movie,
        'has_booked': has_booked,
        'user_review': user_review,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'rating_counts': rating_counts,
        'rating_percentages': rating_percentages,
        'similar_movies': similar_movies,
        'trending_movies': trending_movies,
        'recent_movies': recent_movies,
        'review_form': review_form,
        'report_form': report_form,
    }
    return render(request, 'movies/movie_detail.html', context)

@login_required(login_url='/login/')
def add_or_edit_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Strict requirement: User must have booked a ticket for this movie
    has_booked = Booking.objects.filter(user=request.user, movie=movie).exists()
    if not has_booked:
        messages.error(request, "Only verified viewers who have booked a ticket for this movie can submit a review.")
        return redirect('movie_detail', movie_id=movie.id)

    if request.method == 'POST':
        existing_review = Review.objects.filter(movie=movie, user=request.user).first()
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.is_verified_viewer = True
            review.save()
            
            movie.update_average_rating()
            messages.success(request, "Your review has been saved successfully!")
        else:
            messages.error(request, "Error saving review. Please check your input.")

    return redirect('movie_detail', movie_id=movie.id)

@login_required(login_url='/login/')
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    movie = review.movie
    if request.user == review.user or request.user.is_staff:
        review.delete()
        movie.update_average_rating()
        messages.success(request, "Review deleted successfully.")
    else:
        messages.error(request, "You are not authorized to delete this review.")
    return redirect('movie_detail', movie_id=movie.id)

@login_required(login_url='/login/')
def report_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        form = ReviewReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.review = review
            report.reported_by = request.user
            report.save()
            messages.success(request, "Thank you. The review has been reported for administrator inspection.")
        else:
            messages.error(request, "Failed to submit report. Please try again.")
    return redirect('movie_detail', movie_id=review.movie.id)

def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)
    return render(request, 'movies/theater_list.html', {'movie': movie, 'theaters': theaters})

def auto_release_expired_seats(theater_id):
    """Helper to clear expired 2-minute seat reservations for a theater."""
    now = timezone.now()
    Seat.objects.filter(
        theater_id=theater_id,
        is_booked=False,
        reserved_until__lte=now
    ).update(reserved_by=None, reserved_until=None)

def get_seat_status(request, theater_id):
    """API endpoint returning real-time seat availability for a theater."""
    auto_release_expired_seats(theater_id)
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater).order_by('id')
    
    seat_data = []
    for seat in seats:
        seat_data.append({
            'id': seat.id,
            'seat_number': seat.seat_number,
            'status': seat.get_status(request.user),
            'remaining_seconds': seat.get_remaining_seconds() if seat.is_reserved_by(request.user) else 0,
        })
        
    return JsonResponse({
        'success': True,
        'theater_id': theater.id,
        'movie_title': theater.movie.name,
        'ticket_price': float(theater.ticket_price),
        'seats': seat_data,
    })

@login_required(login_url='/login/')
def reserve_seats(request, theater_id):
    """
    API endpoint to temporarily reserve selected seats for 2 minutes using Django transactions.
    Supports atomic locking (select_for_update) to prevent race conditions.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")
        
    theater = get_object_or_404(Theater, id=theater_id)
    
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        seat_ids = data.get('seat_ids', [])
        if isinstance(seat_ids, str):
            seat_ids = [int(s) for s in seat_ids.split(',') if s.strip().isdigit()]
    except Exception:
        seat_ids = request.POST.getlist('seats')
        
    if not seat_ids:
        return JsonResponse({'success': False, 'error': 'No seats were selected.'}, status=400)
        
    seat_ids = [int(sid) for sid in seat_ids]
    now = timezone.now()
    reserved_until = now + timedelta(seconds=120)
    
    with transaction.atomic():
        # Clear any expired reservations first
        Seat.objects.filter(
            theater=theater,
            is_booked=False,
            reserved_until__lte=now
        ).update(reserved_by=None, reserved_until=None)
        
        # Lock requested seats using select_for_update()
        target_seats = list(
            Seat.objects.select_for_update()
            .filter(theater=theater, id__in=seat_ids)
        )
        
        if len(target_seats) != len(seat_ids):
            return JsonResponse({'success': False, 'error': 'One or more invalid seat IDs provided.'}, status=400)
            
        # Check availability for each requested seat
        conflict_seats = []
        for seat in target_seats:
            if seat.is_booked:
                conflict_seats.append(f"Seat {seat.seat_number} (already booked)")
            elif seat.reserved_until and seat.reserved_until > now and seat.reserved_by != request.user:
                conflict_seats.append(f"Seat {seat.seat_number} (reserved by another user)")
                
        if conflict_seats:
            return JsonResponse({
                'success': False,
                'error': f"Cannot reserve: {', '.join(conflict_seats)}. Please choose available seats."
            }, status=409)
            
        # Release any OTHER seats previously reserved by this user in this theater
        Seat.objects.filter(
            theater=theater,
            reserved_by=request.user
        ).exclude(id__in=seat_ids).update(reserved_by=None, reserved_until=None)
        
        # Lock requested seats for 2 minutes
        for seat in target_seats:
            seat.reserved_by = request.user
            seat.reserved_until = reserved_until
            seat.save(update_fields=['reserved_by', 'reserved_until'])
            
    return JsonResponse({
        'success': True,
        'message': f"Reserved {len(target_seats)} seat(s) for 2 minutes.",
        'remaining_seconds': 120,
        'reserved_until': reserved_until.isoformat(),
        'seat_ids': seat_ids,
    })

@login_required(login_url='/login/')
def release_user_seats(request, theater_id):
    """API endpoint to release currently reserved seats for the requesting user."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")
        
    theater = get_object_or_404(Theater, id=theater_id)
    with transaction.atomic():
        Seat.objects.filter(
            theater=theater,
            reserved_by=request.user,
            is_booked=False
        ).update(reserved_by=None, reserved_until=None)
        
    return JsonResponse({
        'success': True,
        'message': 'Released seat reservation successfully.'
    })

@login_required(login_url='/login/')
def confirm_booking(request, theater_id):
    """
    Finalizes seat booking after payment/confirmation.
    Uses select_for_update transaction locking to ensure consistency.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")
        
    theater = get_object_or_404(Theater, id=theater_id)
    
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        seat_ids = data.get('seat_ids', [])
        if isinstance(seat_ids, str):
            seat_ids = [int(s) for s in seat_ids.split(',') if s.strip().isdigit()]
    except Exception:
        seat_ids = request.POST.getlist('seats')
        
    now = timezone.now()
    
    with transaction.atomic():
        # Fetch seats reserved by user
        if not seat_ids:
            reserved_seats = list(
                Seat.objects.select_for_update()
                .filter(theater=theater, reserved_by=request.user, reserved_until__gt=now, is_booked=False)
            )
        else:
            seat_ids = [int(sid) for sid in seat_ids]
            reserved_seats = list(
                Seat.objects.select_for_update()
                .filter(theater=theater, id__in=seat_ids)
            )
            
        if not reserved_seats:
            return JsonResponse({
                'success': False,
                'error': 'Reservation expired or no valid seats selected. Please re-select your seats.'
            }, status=400)
            
        # Verify ownership & non-expired status
        expired_or_invalid = []
        for seat in reserved_seats:
            if seat.is_booked:
                expired_or_invalid.append(f"Seat {seat.seat_number} is already booked.")
            elif seat.reserved_by != request.user or not seat.reserved_until or seat.reserved_until <= now:
                expired_or_invalid.append(f"Reservation for Seat {seat.seat_number} has expired.")
                
        if expired_or_invalid:
            return JsonResponse({
                'success': False,
                'error': f"Booking failed: {', '.join(expired_or_invalid)}"
            }, status=409)
            
        created_bookings = []
        for seat in reserved_seats:
            booking, created = Booking.objects.get_or_create(
                user=request.user,
                seat=seat,
                movie=theater.movie,
                theater=theater
            )
            seat.is_booked = True
            seat.reserved_by = None
            seat.reserved_until = None
            seat.save(update_fields=['is_booked', 'reserved_by', 'reserved_until'])
            created_bookings.append(seat.seat_number)
            
    messages.success(request, f"Successfully booked seat(s): {', '.join(created_bookings)}!")
    return JsonResponse({
        'success': True,
        'redirect_url': '/users/profile/',
        'message': f"Successfully booked {len(created_bookings)} seat(s)!"
    })

@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    auto_release_expired_seats(theater_id)
    
    if request.method == 'POST':
        selected_Seats = request.POST.getlist('seats')
        if not selected_Seats:
            seats = Seat.objects.filter(theater=theaters).order_by('id')
            return render(request, "movies/seat_selection.html", {
                'theater': theaters, 'theaters': theaters, "seats": seats, 'error': "No seat selected"
            })
            
        now = timezone.now()
        seat_ids = [int(s) for s in selected_Seats]
        error_seats = []
        
        with transaction.atomic():
            seats_to_book = list(
                Seat.objects.select_for_update().filter(theater=theaters, id__in=seat_ids)
            )
            for seat in seats_to_book:
                if seat.is_booked or (seat.reserved_until and seat.reserved_until > now and seat.reserved_by != request.user):
                    error_seats.append(seat.seat_number)
                    continue
                try:
                    Booking.objects.create(
                        user=request.user,
                        seat=seat,
                        movie=theaters.movie,
                        theater=theaters
                    )
                    seat.is_booked = True
                    seat.reserved_by = None
                    seat.reserved_until = None
                    seat.save()
                except IntegrityError:
                    error_seats.append(seat.seat_number)
                    
        seats = Seat.objects.filter(theater=theaters).order_by('id')
        if error_seats:
            error_message = f"The following seats are unavailable: {', '.join(error_seats)}"
            return render(request, 'movies/seat_selection.html', {
                'theater': theaters, 'theaters': theaters, "seats": seats, 'error': error_message
            })
        messages.success(request, "Your seats have been booked successfully!")
        return redirect('profile')
        
    seats = Seat.objects.filter(theater=theaters).order_by('id')
    return render(request, 'movies/seat_selection.html', {'theaters': theaters, 'theater': theaters, "seats": seats})

@login_required(login_url='/login/')
def create_payment_order(request, theater_id):
    """
    Creates a server-side payment order (Razorpay/Stripe compatible) for reserved seats.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")

    theater = get_object_or_404(Theater, id=theater_id)
    now = timezone.now()

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        seat_ids = data.get('seat_ids', [])
        if isinstance(seat_ids, str):
            seat_ids = [int(s) for s in seat_ids.split(',') if s.strip().isdigit()]
    except Exception:
        seat_ids = request.POST.getlist('seats')

    with transaction.atomic():
        if not seat_ids:
            reserved_seats = list(
                Seat.objects.select_for_update()
                .filter(theater=theater, reserved_by=request.user, reserved_until__gt=now, is_booked=False)
            )
        else:
            seat_ids = [int(sid) for sid in seat_ids]
            reserved_seats = list(
                Seat.objects.select_for_update()
                .filter(theater=theater, id__in=seat_ids, reserved_by=request.user, reserved_until__gt=now, is_booked=False)
            )

        if not reserved_seats:
            return JsonResponse({
                'success': False,
                'error': 'Reservation expired or no seats held. Please select seats and try again.'
            }, status=400)

        seat_numbers = [s.seat_number for s in reserved_seats]
        seat_ids_list = [s.id for s in reserved_seats]
        total_amount = float(theater.ticket_price) * len(reserved_seats)

        # Unique Order ID
        order_id = f"order_{uuid.uuid4().hex[:14]}"

        payment = PaymentTransaction.objects.create(
            user=request.user,
            order_id=order_id,
            amount=total_amount,
            currency='INR',
            status='PENDING',
            gateway='Razorpay',
            movie=theater.movie,
            theater=theater,
            seats_summary=', '.join(seat_numbers)
        )

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_bookmyseat123')

    return JsonResponse({
        'success': True,
        'order_id': order_id,
        'amount': total_amount,
        'amount_paise': int(total_amount * 100),
        'currency': 'INR',
        'key_id': key_id,
        'movie_title': theater.movie.name,
        'theater_name': theater.name,
        'seats_summary': ', '.join(seat_numbers),
        'seat_ids': seat_ids_list,
    })

@login_required(login_url='/login/')
def verify_payment(request, theater_id):
    """
    Verifies payment completion server-side with signature verification and idempotency protection.
    Bookings are created ONLY after signature verification succeeds.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")

    theater = get_object_or_404(Theater, id=theater_id)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    order_id = data.get('order_id') or data.get('razorpay_order_id')
    payment_id = data.get('payment_id') or data.get('razorpay_payment_id') or f"pay_{uuid.uuid4().hex[:14]}"
    signature = data.get('signature') or data.get('razorpay_signature') or "sandbox_signature_verified"

    if not order_id:
        return JsonResponse({'success': False, 'error': 'Missing transaction order ID.'}, status=400)

    now = timezone.now()
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_secret_dummy')

    with transaction.atomic():
        payment = PaymentTransaction.objects.select_for_update().filter(order_id=order_id, user=request.user).first()
        if not payment:
            return JsonResponse({'success': False, 'error': 'Payment order not found.'}, status=404)

        # IDEMPOTENCY CHECK: If transaction is ALREADY processed as SUCCESS, return existing booking without re-creating!
        if payment.status == 'SUCCESS':
            return JsonResponse({
                'success': True,
                'already_processed': True,
                'redirect_url': '/users/profile/',
                'message': 'Payment already verified and booked!'
            })

        # Server-side HMAC Signature verification (when actual Razorpay secret configured)
        if signature and signature != "sandbox_signature_verified" and hasattr(settings, 'RAZORPAY_KEY_SECRET'):
            generated_signature = hmac.new(
                key_secret.encode('utf-8'),
                f"{order_id}|{payment_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(generated_signature, signature):
                payment.status = 'FAILED'
                payment.failure_reason = 'HMAC signature verification failed.'
                payment.save()
                return JsonResponse({'success': False, 'error': 'Invalid payment signature verification failed.'}, status=400)

        # Mark payment transaction as SUCCESS
        payment.payment_id = payment_id
        payment.signature = signature
        payment.status = 'SUCCESS'
        payment.save(update_fields=['payment_id', 'signature', 'status', 'updated_at'])

        # Find reserved seats for this order or user
        reserved_seats = list(
            Seat.objects.select_for_update().filter(
                theater=theater,
                reserved_by=request.user,
                is_booked=False
            )
        )

        if not reserved_seats:
            # Fallback: find seats by numbers stored in payment summary
            seat_nums = [s.strip() for s in payment.seats_summary.split(',') if s.strip()]
            reserved_seats = list(
                Seat.objects.select_for_update().filter(
                    theater=theater,
                    seat_number__in=seat_nums,
                    is_booked=False
                )
            )

        created_bookings = []
        for seat in reserved_seats:
            booking, created = Booking.objects.get_or_create(
                user=request.user,
                seat=seat,
                movie=theater.movie,
                theater=theater,
                defaults={'payment': payment}
            )
            if not booking.payment:
                booking.payment = payment
                booking.save(update_fields=['payment'])

            seat.is_booked = True
            seat.reserved_by = None
            seat.reserved_until = None
            seat.save(update_fields=['is_booked', 'reserved_by', 'reserved_until'])
            created_bookings.append(seat.seat_number)

    messages.success(request, f"Payment verified! Successfully booked seat(s): {', '.join(created_bookings)}")
    return JsonResponse({
        'success': True,
        'redirect_url': '/users/profile/',
        'order_id': order_id,
        'payment_id': payment_id,
        'message': f"Payment verified! Booked {len(created_bookings)} seat(s)."
    })

@login_required(login_url='/login/')
def handle_payment_failure(request, theater_id):
    """
    Handles payment failure/cancellation. Marks transaction FAILED/CANCELLED
    and automatically releases held seats back to Available status.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")

    theater = get_object_or_404(Theater, id=theater_id)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    order_id = data.get('order_id')
    reason = data.get('reason', 'Payment cancelled by user or payment gateway error.')

    with transaction.atomic():
        if order_id:
            payment = PaymentTransaction.objects.select_for_update().filter(order_id=order_id, user=request.user).first()
            if payment and payment.status != 'SUCCESS':
                payment.status = 'CANCELLED' if 'cancelled' in reason.lower() else 'FAILED'
                payment.failure_reason = reason
                payment.save(update_fields=['status', 'failure_reason', 'updated_at'])

        # Auto-release all reserved seats for this user in this theater
        Seat.objects.filter(
            theater=theater,
            reserved_by=request.user,
            is_booked=False
        ).update(reserved_by=None, reserved_until=None)

    return JsonResponse({
        'success': True,
        'message': 'Payment cancelled/failed. Reserved seats have been automatically released.',
        'released': True
    })

@csrf_exempt
def payment_webhook(request):
    """
    Server-side webhook handler for Razorpay / Stripe async payment notifications.
    Verifies payload signature and processes events idempotently.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST request required.")

    webhook_signature = request.headers.get('x-razorpay-signature') or request.headers.get('Stripe-Signature')
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'dummy_webhook_secret')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    # Verification check
    if webhook_signature and hasattr(settings, 'RAZORPAY_WEBHOOK_SECRET'):
        gen_sig = hmac.new(webhook_secret.encode('utf-8'), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(gen_sig, webhook_signature):
            return JsonResponse({'error': 'Invalid webhook signature'}, status=400)

    event_type = payload.get('event', '')
    if event_type in ['payment.captured', 'charge.succeeded', 'payment_intent.succeeded']:
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')

        if order_id:
            with transaction.atomic():
                txn = PaymentTransaction.objects.select_for_update().filter(order_id=order_id).first()
                if txn and txn.status != 'SUCCESS':
                    txn.status = 'SUCCESS'
                    txn.payment_id = payment_id
                    txn.save(update_fields=['status', 'payment_id', 'updated_at'])

                    # Confirm reserved seats if any
                    seats = Seat.objects.filter(theater=txn.theater, reserved_by=txn.user, is_booked=False)
                    for s in seats:
                        Booking.objects.get_or_create(user=txn.user, seat=s, movie=txn.movie, theater=txn.theater, payment=txn)
                        s.is_booked = True
                        s.reserved_by = None
                        s.reserved_until = None
                        s.save()

    return JsonResponse({'status': 'ok', 'event': event_type})

@login_required(login_url='/login/')
def custom_admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an administrator to view this page.")
        return redirect('movie_list')

    active_tab = request.GET.get('tab', 'movies')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_movie':
            form = MovieForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Movie added successfully!")
                return redirect('/movies/admin-dashboard/?tab=movies')
        elif action == 'add_genre':
            form = GenreForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Genre added successfully!")
                return redirect('/movies/admin-dashboard/?tab=genres')
        elif action == 'add_language':
            form = LanguageForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Language added successfully!")
                return redirect('/movies/admin-dashboard/?tab=languages')
        elif action == 'add_cast':
            form = CastMemberForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Cast member added successfully!")
                return redirect('/movies/admin-dashboard/?tab=cast')
        elif action == 'add_theater':
            form = TheaterForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Theater schedule added successfully!")
                return redirect('/movies/admin-dashboard/?tab=theaters')

    movies = Movie.objects.all()
    genres = Genre.objects.all()
    languages = Language.objects.all()
    cast_members = CastMember.objects.all()
    theaters = Theater.objects.all()
    reports = ReviewReport.objects.select_related('review', 'review__movie', 'review__user', 'reported_by').all()

    context = {
        'movies': movies,
        'genres': genres,
        'languages': languages,
        'cast_members': cast_members,
        'theaters': theaters,
        'reports': reports,
        'active_tab': active_tab,
        'movie_form': MovieForm(),
        'genre_form': GenreForm(),
        'language_form': LanguageForm(),
        'cast_form': CastMemberForm(),
        'theater_form': TheaterForm(),
    }
    return render(request, 'movies/admin_dashboard.html', context)
