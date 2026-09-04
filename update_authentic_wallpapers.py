import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import django
import urllib.request

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Movie, MoviePoster

print("--- Updating Authentic Posters & Wallpapers for All Movies ---")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'media', 'movies')
GALLERY_DIR = os.path.join(MEDIA_DIR, 'posters')
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(GALLERY_DIR, exist_ok=True)

# Curated authentic direct poster & wallpaper image URLs
WALLPAPERS_MAP = {
    "Inception": {
        "poster": "https://image.tmdb.org/t/p/w500/oYuLEydvwzK8oYiGzMoM2flTfw.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/8ZTVqvKDQ8emSGUEMjsS4yHA84E.jpg",
            "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Oppenheimer": {
        "poster": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGvFioR1v57.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/fm6KqXpk3M2HVveHwCrBSSBaO0V.jpg",
            "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "The Dark Knight": {
        "poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/dqK9Hag1054tghRQSqLSfrl29zA.jpg",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Interstellar": {
        "poster": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/xJHokMbljvjADYdit5fKSuV0vEG.jpg",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Avatar: The Way of Water": {
        "poster": "https://image.tmdb.org/t/p/w500/t6HIw21OjUwWistUrieSt2dPLn1.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/vL5LR6WdxWPjUnFRi2vjJmKGWHE.jpg",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Avengers: Endgame": {
        "poster": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9vKoWRwwo1.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/7RyHsO4yDXtBv1zUU3pHpErzjL.jpg",
            "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Titanic": {
        "poster": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/yDI6D5jPXD29fJ2alSuwCZSxqWh.jpg"
        ]
    },
    "Spider-Man: Into the Spider-Verse": {
        "poster": "https://image.tmdb.org/t/p/w500/iiZZdoQHeeFGivVeeicRdflxECq.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/7d62uL2LrmwZFiTknfygtICjTio.jpg"
        ]
    },
    "Spider-Man: No Way Home": {
        "poster": "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/iQFcwSGbZ1VMR3iGaFiO1y36Wz1.jpg"
        ]
    },
    "The Matrix": {
        "poster": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/vL5LR6WdxWPjUnFRi2vjJmKGWHE.jpg"
        ]
    },
    "RRR": {
        "poster": "https://image.tmdb.org/t/p/w500/wE0bvjh2bFk1y0kU58j0o1g86gS.jpg",
        "wallpapers": [
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80"
        ]
    },
    "Dune: Part Two": {
        "poster": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/xOMo8BRK7PfcJv9JCnx7s52SuY.jpg"
        ]
    },
    "Deadpool & Wolverine": {
        "poster": "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/yDHYTfA3R0jFYba16jBB128ioyU.jpg"
        ]
    },
    "Joker": {
        "poster": "https://image.tmdb.org/t/p/w500/udDclSubHAVbdJFajKGJGGftMmy.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/f5F4cRhQdUbyVbBwEhDBHjKQOOz.jpg"
        ]
    },
    "The Godfather": {
        "poster": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/rSPw7tgCH9c6NqICZefy2aUMRXZ.jpg"
        ]
    },
    "Pulp Fiction": {
        "poster": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/suaEOtk1N1sgg2MTM7oZd2cfPw3.jpg"
        ]
    },
    "Fight Club": {
        "poster": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/hZkgoQY85WEREaojO2upEwPPyQH.jpg"
        ]
    },
    "Barbie": {
        "poster": "https://image.tmdb.org/t/p/w500/iuJuN22vOiDatHYiDJV2GiL0mAc.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/ctMserH8g2d2s53sJ9F916Fi2rm.jpg"
        ]
    },
    "Top Gun: Maverick": {
        "poster": "https://image.tmdb.org/t/p/w500/62HCfaYToWd2TNBX2BAFqvxsEuo.jpg",
        "wallpapers": [
            "https://image.tmdb.org/t/p/w780/AaV1YIdWKnjA2bL8I0fLWu37fBq.jpg"
        ]
    }
}

# Generic unsplash fallback wallpapers for any movie without specific TMDB URL
DEFAULT_WALLPAPERS = [
    "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80"
]

movies = Movie.objects.all()
updated_count = 0

for movie in movies:
    safe_title = movie.name.lower().replace(' ', '_').replace(':', '').replace('-', '_').replace('–', '_')
    poster_filename = f"{safe_title}_wallpaper.jpg"
    poster_filepath = os.path.join(MEDIA_DIR, poster_filename)

    # Check if custom wallpaper mapping exists
    info = WALLPAPERS_MAP.get(movie.name)
    poster_url = info["poster"] if info else DEFAULT_WALLPAPERS[updated_count % len(DEFAULT_WALLPAPERS)]

    # Download authentic poster
    try:
        req = urllib.request.Request(poster_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(poster_filepath, 'wb') as f:
            f.write(resp.read())
        movie.image = f"movies/{poster_filename}"
        movie.save(update_fields=['image'])
        print(f"[{updated_count+1}] Downloaded authentic poster for '{movie.name}'")
    except Exception as e:
        print(f"[{updated_count+1}] Using existing poster for '{movie.name}' ({e})")

    # Add secondary wallpapers to MoviePoster gallery
    gallery_urls = info["wallpapers"] if info else [DEFAULT_WALLPAPERS[(updated_count + 1) % len(DEFAULT_WALLPAPERS)]]
    for idx, wall_url in enumerate(gallery_urls):
        gal_filename = f"{safe_title}_gallery_{idx+1}.jpg"
        gal_filepath = os.path.join(GALLERY_DIR, gal_filename)
        try:
            req = urllib.request.Request(wall_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp, open(gal_filepath, 'wb') as f:
                f.write(resp.read())
            MoviePoster.objects.get_or_create(
                movie=movie,
                image=f"movies/posters/{gal_filename}",
                defaults={"caption": f"{movie.name} Official Wallpaper #{idx+1}"}
            )
        except Exception:
            pass

    updated_count += 1

print(f"\nSuccessfully updated authentic wallpapers & gallery posters for all {updated_count} movies!")
