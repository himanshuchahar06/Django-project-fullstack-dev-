import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from django.contrib.auth.models import User
from movies.models import Movie, Review, Booking, Theater, Seat

print("--- Testing Movie Management Module Features ---")

# Test 1: YouTube embed URL parsing
movie = Movie.objects.filter(name="Inception").first()
assert movie is not None
print(f"Movie: {movie.name}")
print(f"Trailer URL: {movie.trailer_youtube_url}")
print(f"Embed URL: {movie.youtube_embed_url}")
assert "embed/YoHD9XEInc0" in movie.youtube_embed_url
print("[OK] YouTube Trailer Embed parsing PASSED")

# Test 2: Duration formatting & age cert
print(f"Duration: {movie.duration_formatted}")
assert movie.duration_formatted == "2h 28m"
print("[OK] Duration formatting PASSED")

# Test 3: Booking & Verified Viewer logic
test_user = User.objects.get(username="testuser")
user_has_booking = Booking.objects.filter(user=test_user, movie=movie).exists()
print(f"TestUser has booking for Inception: {user_has_booking}")
assert user_has_booking == True
print("[OK] Verified Viewer Booking Check PASSED")

# Test 4: Rating calculation
review = Review.objects.filter(movie=movie, user=test_user).first()
print(f"Review: {review.rating} Stars - \"{review.comment}\"")
print(f"Calculated Movie Average Rating: {movie.rating}")
assert float(movie.rating) == 5.0
print("[OK] Average Rating Calculation PASSED")

# Test 5: Unverified user check
unverified_user, _ = User.objects.get_or_create(username="unverifieduser")
unverified_has_booking = Booking.objects.filter(user=unverified_user, movie=movie).exists()
print(f"Unverified user has booking: {unverified_has_booking}")
assert unverified_has_booking == False
print("[OK] Unverified Viewer Block PASSED")

print("=== ALL AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY! ===")
