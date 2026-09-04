import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Movie, Review

print("--- Scaling All Movie & Review Ratings out of 10 ---")

# 1. Scale existing Reviews
reviews = Review.objects.all()
for rev in reviews:
    if rev.rating <= 5:
        old_val = rev.rating
        rev.rating = min(rev.rating * 2, 10)
        rev.save()
        print(f"Scaled Review for '{rev.movie.name}' by {rev.user.username}: {old_val}/5 -> {rev.rating}/10")

# 2. Scale Movies
movies = Movie.objects.all()
count = 0
for movie in movies:
    old_rating = float(movie.rating)
    if old_rating <= 5.0 and old_rating > 0:
        new_rating = round(min(old_rating * 2.0, 10.0), 1)
        movie.rating = new_rating
        movie.save(update_fields=['rating'])
        count += 1
        print(f"[{count}] Scaled Movie '{movie.name}': {old_rating}/5.0 -> {new_rating}/10.0")
    elif movie.reviews.exists():
        movie.update_average_rating()

print("\nSuccessfully updated all movie ratings to scale out of 10.0!")
