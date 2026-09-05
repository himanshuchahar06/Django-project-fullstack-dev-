from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('<int:movie_id>/review/', views.add_or_edit_review, name='add_or_edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('review/<int:review_id>/report/', views.report_review, name='report_review'),
    path('<int:movie_id>/theaters', views.theater_list, name='theater_list'),
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),
    path('theater/<int:theater_id>/seat-status/', views.get_seat_status, name='get_seat_status'),
    path('theater/<int:theater_id>/reserve-seats/', views.reserve_seats, name='reserve_seats'),
    path('theater/<int:theater_id>/release-seats/', views.release_user_seats, name='release_user_seats'),
    path('theater/<int:theater_id>/confirm-booking/', views.confirm_booking, name='confirm_booking'),
    path('admin-dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
]