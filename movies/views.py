from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q, Count
from .models import (
    Movie, Theater, Seat, Booking, Genre, Language, 
    CastMember, MoviePoster, Review, ReviewReport
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

@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)
    if request.method == 'POST':
        selected_Seats = request.POST.getlist('seats')
        error_seats = []
        if not selected_Seats:
            return render(request, "movies/seat_selection.html", {'theater': theaters, 'theaters': theaters, "seats": seats, 'error': "No seat selected"})
        for seat_id in selected_Seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theaters)
            if seat.is_booked:
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
                seat.save()
            except IntegrityError:
                error_seats.append(seat.seat_number)
        if error_seats:
            error_message = f"The following seats are already booked: {', '.join(error_seats)}"
            return render(request, 'movies/seat_selection.html', {'theater': theaters, 'theaters': theaters, "seats": seats, 'error': error_message})
        return redirect('profile')
    return render(request, 'movies/seat_selection.html', {'theaters': theaters, "seats": seats})

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
