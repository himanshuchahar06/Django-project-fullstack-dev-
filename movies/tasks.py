import logging
from django.core.mail import EmailMessage
from django.conf import settings
from .models import PaymentTransaction
from .ticket_generator import generate_pdf_ticket

logger = logging.getLogger(__name__)

def _send_ticket_email_impl(transaction_id, retry_func=None):
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
        if retry_func:
            try:
                return retry_func(exc)
            except Exception:
                pass
        return f"Failed sending email: {exc}"

try:
    from celery import shared_task
    @shared_task(bind=True, max_retries=3, default_retry_delay=5)
    def send_ticket_email_task(self, transaction_id):
        return _send_ticket_email_impl(transaction_id, retry_func=lambda exc: self.retry(exc=exc))
except Exception:
    def send_ticket_email_task(transaction_id):
        return _send_ticket_email_impl(transaction_id)

def dispatch_ticket_email_async(transaction_id):
    """Helper to trigger task asynchronously or fall back safely if Celery / Redis is unconfigured or offline."""
    try:
        if hasattr(send_ticket_email_task, 'delay'):
            send_ticket_email_task.delay(transaction_id)
        else:
            _send_ticket_email_impl(transaction_id)
    except Exception:
        # Fallback to sync execution so checkout never blocks or fails
        try:
            _send_ticket_email_impl(transaction_id)
        except Exception as e:
            logger.error(f"Fallback email execution error: {e}")

