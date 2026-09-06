import logging
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .models import PaymentTransaction
from .ticket_generator import generate_pdf_ticket

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_ticket_email_task(self, transaction_id):
    """
    Asynchronous Celery task to generate PDF ticket and email it to the user.
    Retries up to 3 times automatically on failure without blocking the HTTP request thread.
    """
    try:
        txn = PaymentTransaction.objects.select_related('movie', 'theater', 'user').get(id=transaction_id)
        if not txn.user.email:
            logger.warning(f"No email address found for user {txn.user.username}. Skipping email sending.")
            return f"No email for user {txn.user.username}"

        pdf_bytes = generate_pdf_ticket(txn)

        subject = f"🎟️ Your BookMySeat Ticket Confirmation - Order #{txn.order_id}"
        body = (
            f"Dear {txn.user.get_full_name() or txn.user.username},\n\n"
            f"Thank you for booking with BookMySeat!\n"
            f"Your booking for '{txn.movie.name}' at '{txn.theater.name}' on {txn.theater.time.strftime('%A, %d %b %Y at %I:%M %p')} is CONFIRMED.\n\n"
            f"Booked Seats: {txn.seats_summary}\n"
            f"Order Reference: {txn.order_id}\n"
            f"Amount Paid: ₹{txn.amount:.2f} {txn.currency}\n\n"
            f"Please find your official E-Ticket PDF with embedded QR Code attached to this email.\n\n"
            f"Best regards,\n"
            f"The BookMySeat Team"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bookmyseat.com'),
            to=[txn.user.email]
        )

        email.attach(
            filename=f"BookMySeat_Ticket_{txn.order_id}.pdf",
            content=pdf_bytes,
            mimetype="application/pdf"
        )

        email.send(fail_silently=False)
        logger.info(f"Successfully sent ticket email for order {txn.order_id} to {txn.user.email}")
        return f"Email sent to {txn.user.email}"
    except Exception as exc:
        logger.error(f"Error sending ticket email for txn #{transaction_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except Exception:
            return f"Failed sending email after retries: {exc}"

def dispatch_ticket_email_async(transaction_id):
    """Helper to trigger task asynchronously or fall back safely if Celery is unconfigured."""
    try:
        send_ticket_email_task.delay(transaction_id)
    except Exception:
        # Fallback to sync or thread execution so checkout never blocks or fails
        try:
            send_ticket_email_task(transaction_id)
        except Exception as e:
            logger.error(f"Fallback email execution error: {e}")
