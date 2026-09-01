import re
from django.db import models
from django.contrib.auth.models import User 
from django.db.models import Avg

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CastMember(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100, help_text="Role e.g. Director, Lead Actor, Supporting Actor")
    photo = models.ImageField(upload_to="cast/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.role})"

AGE_CERTIFICATION_CHOICES = [
    ('U', 'U - Universal'),
    ('UA', 'UA - Parental Guidance'),
    ('A', 'A - Adults Only'),
    ('S', 'S - Specialized Groups'),
    ('PG-13', 'PG-13'),
    ('R', 'R'),
]

class Movie(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="movies/")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    cast = models.TextField(blank=True, null=True, help_text="Legacy cast summary text")
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=120, help_text="Duration in minutes")
    age_certification = models.CharField(max_length=10, choices=AGE_CERTIFICATION_CHOICES, default='UA')
    trailer_youtube_url = models.URLField(blank=True, null=True, help_text="YouTube video URL or embed URL e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    release_date = models.DateField(blank=True, null=True)
    is_trending = models.BooleanField(default=False)

    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    languages = models.ManyToManyField(Language, related_name='movies', blank=True)
    cast_members = models.ManyToManyField(CastMember, related_name='movies', blank=True)

    class Meta:
        ordering = ['-release_date', 'name']

    def __str__(self):
        return self.name

    @property
    def youtube_embed_url(self):
        if not self.trailer_youtube_url:
            return None
        url = self.trailer_youtube_url.strip()
        if 'embed/' in url:
            return url
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"
        return url

    @property
    def duration_formatted(self):
        if not self.duration_minutes:
            return "N/A"
        hrs = self.duration_minutes // 60
        mins = self.duration_minutes % 60
        if hrs > 0:
            return f"{hrs}h {mins}m"
        return f"{mins}m"

    def update_average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg is not None:
            self.rating = round(avg, 1)
        else:
            self.rating = 0.0
        self.save(update_fields=['rating'])

class MoviePoster(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='additional_posters')
    image = models.ImageField(upload_to="movies/posters/")
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Poster for {self.movie.name}"

class Theater(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField()
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2, default=250.00)

    class Meta:
        ordering = ['time']

    def __str__(self):
        return f'{self.name} - {self.movie.name} at {self.time.strftime("%Y-%m-%d %H:%M") if self.time else ""}'

class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Booking by {self.user.username} for {self.seat.seat_number} at {self.theater.name}'

class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_reviews')
    rating = models.PositiveIntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)])
    comment = models.TextField()
    is_verified_viewer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('movie', 'user')

    def __str__(self):
        return f'{self.user.username} review for {self.movie.name} ({self.rating} stars)'

class ReviewReport(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report on review #{self.review.id} by {self.reported_by.username}'