import logging

from trionyx.tasks import BaseTask, shared_task
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .models import Invoice
from .conf import settings

logger = logging.getLogger(__name__)


class InvoicePublishTask(BaseTask):
    """Mass update task"""

    name = 'invoice_publish'

    def run(self):
        self.set_progress(10)
        self.add_output(_('Creating invoice PDF'))
        self.get_object().create_pdf()

        self.set_progress(80)
        self.add_output(_('Sending invoice'))
        self.get_object().send()


@shared_task
def send_reminders():
    due_date = timezone.now() + timezone.timedelta(days=settings.INVOICE_REMINDER_DAYS_BEFORE)
    invoices = Invoice.objects.filter(
        status=Invoice.STATUS_SEND,
        send_reminder_date__isnull=True,
        due_date__lte=due_date)

    for invoice in invoices:
        try:
            invoice.send_reminder()
            invoice.send_reminder_date = timezone.now()
            invoice.save(update_fields=['send_reminder_date'])
        except Exception as e:
            logger.exception(e)


@shared_task
def send_past_dues():
    due_date = timezone.now() - timezone.timedelta(days=settings.INVOICE_SEND_DUE_DAYS_AFTER)
    invoices = Invoice.objects.filter(
        status_in=[Invoice.STATUS_SEND, Invoice.STATUS_OVERDUE],
        send_past_due_date__isnull=True,
        due_date__lte=due_date)

    for invoice in invoices:
        try:
            invoice.send_past_due()
            invoice.send_past_due_date = timezone.now()
            invoice.save(update_fields=['send_past_due_date'])
        except Exception as e:
            logger.exception(e)


@shared_task
def mark_overdue_invoices():
    Invoice.objects.filter(status=Invoice.STATUS_SEND, due_date__lt=timezone.now()).update(
        status=Invoice.STATUS_OVERDUE,
    )
