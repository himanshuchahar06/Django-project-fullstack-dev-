import os
import sys
import time
import django

# Setup Django environment
sys.path.append('.')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'bookmyseat.settings'
django.setup()

from django.contrib.auth.models import User
from movies.models import Movie, Theater, Seat, Booking, PaymentTransaction
from movies.views import get_admin_analytics_data

def ensure_admin_user():
    """Ensure administrator credentials exist for report & admin testing."""
    # Check if old 'admin' user exists and rename/update, or get/create 'Himanshu'
    old_admin = User.objects.filter(username='admin').first()
    if old_admin:
        old_admin.username = 'Himanshu'
        old_admin.email = 'himanshu@bookmyseat.com'
        old_admin.is_staff = True
        old_admin.is_superuser = True
        old_admin.set_password('Himanshu@1')
        old_admin.save()
        admin_user = old_admin
        status = "Updated existing superuser 'admin' to 'Himanshu'"
    else:
        admin_user, created = User.objects.get_or_create(username='Himanshu', defaults={'email': 'himanshu@bookmyseat.com'})
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('Himanshu@1')
        admin_user.save()
        status = "Created new" if created else "Updated existing"
    print(f"[ADMIN CREDENTIALS] {status}: Username='Himanshu', Password='Himanshu@1'")
    return admin_user

def run_performance_benchmark():
    """Run performance benchmark on get_admin_analytics_data ORM queries."""
    print("--- Running High-Scale Django ORM Analytics Performance Benchmark ---")
    
    total_bookings = Booking.objects.count()
    total_payments = PaymentTransaction.objects.count()
    print(f"Current Database Scale: {total_bookings} Bookings, {total_payments} Payment Transactions")

    start_time = time.time()
    analytics_data = get_admin_analytics_data(preset='all_time')
    elapsed_time = time.time() - start_time

    print(f"\nQuery Execution Time: {elapsed_time:.4f} seconds ({elapsed_time * 1000:.2f} ms)")
    print(f"Sub-second Execution Check: {'PASSED [SUCCESS]' if elapsed_time < 1.0 else 'FAILED'}")
    print("\n--- Summary Performance Insights Generated ---")
    print(f"Daily Revenue: ₹{analytics_data['daily_rev']:.2f}")
    print(f"Weekly Revenue: ₹{analytics_data['weekly_rev']:.2f}")
    print(f"Monthly Revenue: ₹{analytics_data['monthly_rev']:.2f}")
    print(f"Yearly Revenue: ₹{analytics_data['yearly_rev']:.2f}")
    print(f"Total Filtered Revenue: ₹{analytics_data['filtered_rev']:.2f}")
    print(f"Total Bookings Evaluated: {analytics_data['total_bookings_count']}")
    print(f"Theaters Evaluated for Occupancy: {len(analytics_data['theater_occupancy_list'])}")
    print(f"Most Booked Movies Evaluated: {len(analytics_data['most_booked_movies'])}")
    print(f"Cancellation / Failure Rate: {analytics_data['cancellation_rate']}%")

if __name__ == '__main__':
    ensure_admin_user()
    run_performance_benchmark()
