from django.contrib import admin
from .models import (
    Genre, Language, CastMember, Movie, MoviePoster, 
    Theater, Seat, Booking, Review, ReviewReport
)

class MoviePosterInline(admin.TabularInline):
    model = MoviePoster
    extra = 1

class TheaterInline(admin.TabularInline):
    model = Theater
    extra = 1

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(CastMember)
class CastMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role']
    list_filter = ['role']
    search_fields = ['name', 'role']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'age_certification', 'duration_minutes', 'release_date', 'is_trending']
    list_filter = ['age_certification', 'is_trending', 'genres', 'languages', 'release_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['genres', 'languages', 'cast_members']
    inlines = [MoviePosterInline, TheaterInline]

@admin.register(MoviePoster)
class MoviePosterAdmin(admin.ModelAdmin):
    list_display = ['movie', 'caption']
    list_filter = ['movie']

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'movie', 'time', 'ticket_price']
    list_filter = ['movie', 'time']
    search_fields = ['name', 'location']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']
    list_filter = ['is_booked', 'theater']
    search_fields = ['seat_number']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'seat', 'movie', 'theater', 'booked_at']
    list_filter = ['movie', 'theater', 'booked_at']
    search_fields = ['user__username', 'movie__name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'user', 'rating', 'is_verified_viewer', 'created_at', 'updated_at']
    list_filter = ['rating', 'is_verified_viewer', 'created_at']
    search_fields = ['movie__name', 'user__username', 'comment']

@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['review', 'reported_by', 'reason', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__movie__name', 'review__user__username', 'reported_by__username', 'reason']
