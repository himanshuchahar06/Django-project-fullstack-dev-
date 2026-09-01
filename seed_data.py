import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from django.contrib.auth.models import User
from movies.models import Movie, Genre, Language, CastMember, Theater, Seat, Booking, Review

print("Seeding database with sample movie data...")

# Create Genres
action, _ = Genre.objects.get_or_create(name="Action", slug="action")
scifi, _ = Genre.objects.get_or_create(name="Sci-Fi", slug="sci-fi")
drama, _ = Genre.objects.get_or_create(name="Drama", slug="drama")
thriller, _ = Genre.objects.get_or_create(name="Thriller", slug="thriller")

# Create Languages
eng, _ = Language.objects.get_or_create(name="English", code="en")
hin, _ = Language.objects.get_or_create(name="Hindi", code="hi")

# Create Cast Members
cast1, _ = CastMember.objects.get_or_create(name="Christopher Nolan", role="Director", bio="Renowned director")
cast2, _ = CastMember.objects.get_or_create(name="Leonardo DiCaprio", role="Lead Actor", bio="Oscar winning actor")
cast3, _ = CastMember.objects.get_or_create(name="Cillian Murphy", role="Lead Actor", bio="Oppenheimer star")

# Create or Update Movies
m1, _ = Movie.objects.get_or_create(
    name="Inception",
    defaults={
        'description': "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        'duration_minutes': 148,
        'age_certification': 'UA',
        'trailer_youtube_url': "https://www.youtube.com/watch?v=YoHD9XEInc0",
        'release_date': datetime(2010, 7, 16).date(),
        'is_trending': True,
        'rating': 4.8,
    }
)
m1.genres.add(action, scifi, thriller)
m1.languages.add(eng)
m1.cast_members.add(cast1, cast2)

m2, _ = Movie.objects.get_or_create(
    name="Oppenheimer",
    defaults={
        'description': "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
        'duration_minutes': 180,
        'age_certification': 'A',
        'trailer_youtube_url': "https://www.youtube.com/watch?v=uYPbbksJxIg",
        'release_date': datetime(2023, 7, 21).date(),
        'is_trending': True,
        'rating': 4.9,
    }
)
m2.genres.add(drama, thriller)
m2.languages.add(eng)
m2.cast_members.add(cast1, cast3)

# Create Theater & Seats
t1, _ = Theater.objects.get_or_create(
    name="PVR IMAX Downtown",
    movie=m1,
    defaults={
        'location': "Screen 1, City Center",
        'time': datetime.now() + timedelta(days=1),
        'ticket_price': 350.00
    }
)

for seat_no in ['A1', 'A2', 'A3', 'B1', 'B2']:
    Seat.objects.get_or_create(theater=t1, seat_number=seat_no)

# Create Test User & Booking
test_user, created = User.objects.get_or_create(username="testuser")
if created:
    test_user.set_password("pass123")
    test_user.save()

# Book seat A1 for test_user on m1
s1 = Seat.objects.filter(theater=t1, seat_number='A1').first()
if s1 and not s1.is_booked:
    s1.is_booked = True
    s1.save()
    Booking.objects.get_or_create(user=test_user, seat=s1, movie=m1, theater=t1)

# Add verified review
r1, _ = Review.objects.get_or_create(
    movie=m1,
    user=test_user,
    defaults={
        'rating': 5,
        'comment': "Mind-bending masterpiece! The visuals, score, and story are unmatched.",
        'is_verified_viewer': True
    }
)
m1.update_average_rating()

print("Database seeding complete successfully!")
