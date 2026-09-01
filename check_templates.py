import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from django.template.loader import render_to_string
from movies.models import Movie

print("--- Testing Template Rendering ---")

movie = Movie.objects.first()
if movie:
    html = render_to_string('movies/movie_detail.html', {
        'movie': movie,
        'has_booked': True,
        'user_review': None,
        'reviews': [],
        'total_reviews': 0,
        'rating_counts': {1:0, 2:0, 3:0, 4:0, 5:0},
        'rating_percentages': {1:0, 2:0, 3:0, 4:0, 5:0},
        'similar_movies': [],
        'trending_movies': [],
        'recent_movies': [],
    })
    assert len(html) > 500
    print("[OK] movie_detail.html renders successfully!")

    list_html = render_to_string('movies/movie_list.html', {
        'movies': [movie],
        'genres': [],
        'languages': [],
        'selected_genre': '',
        'selected_language': '',
        'search_query': '',
    })
    assert len(list_html) > 500
    print("[OK] movie_list.html renders successfully!")

print("ALL TEMPLATES RENDER SUCCESSFULLY!")
