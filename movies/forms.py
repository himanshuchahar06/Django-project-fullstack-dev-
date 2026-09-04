from django import forms
from .models import Movie, Review, ReviewReport, Genre, Language, CastMember, Theater

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{i}/10 Stars") for i in range(10, 0, -1)],
        widget=forms.Select(attrs={'class': 'form-control bg-dark text-warning border-secondary font-weight-bold'}),
        initial=10
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'rows': 4,
            'placeholder': 'Share your experience, thoughts on plot, acting, visual effects...'
        })
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']

class ReviewReportForm(forms.ModelForm):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'rows': 3,
            'placeholder': 'Explain why this review is inappropriate or spam...'
        })
    )

    class Meta:
        model = ReviewReport
        fields = ['reason']

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            'name', 'image', 'description', 'duration_minutes', 
            'age_certification', 'trailer_youtube_url', 'release_date', 
            'is_trending', 'genres', 'languages', 'cast_members'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark text-light border-secondary', 'rows': 3}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'age_certification': forms.Select(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'trailer_youtube_url': forms.URLInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'type': 'date'}),
            'genres': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'languages': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'cast_members': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
        }

class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'slug': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
        }

class LanguageForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'code': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
        }

class CastMemberForm(forms.ModelForm):
    class Meta:
        model = CastMember
        fields = ['name', 'role', 'photo', 'bio']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'role': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'bio': forms.Textarea(attrs={'class': 'form-control bg-dark text-light border-secondary', 'rows': 2}),
        }

class TheaterForm(forms.ModelForm):
    class Meta:
        model = Theater
        fields = ['name', 'location', 'movie', 'time', 'ticket_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'location': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'movie': forms.Select(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'time': forms.DateTimeInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'type': 'datetime-local'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
        }
