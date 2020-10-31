from django.conf import settings
from trionyx.config import AppSettings
from django.utils.translation import ugettext_lazy as _


settings = AppSettings('INVOICES', {
    'REFERENCE_FORMAT': '{increment_long}',
    'PAYMENT_INSTRUCTIONS': '',
    'PDF_FOOTER': '',
    'PDF_COLOR': settings.TX_THEME_COLOR.replace('-light', ''),
    'HOURLY_PRICE': 60,

    'INVOICE_EMAIL_SUBJECT': _('Invoice {invoice_id}'),
    'INVOICE_EMAIL_REMINDER_SUBJECT': _('Invoice {invoice_id}'),
    'INVOICE_EMAIL_PAST_DUE_SUBJECT': _('Invoice {invoice_id} is past due'),
    'INVOICE_REMINDER_DAYS_BEFORE': 7,
    'INVOICE_SEND_DUE_DAYS_AFTER': 3,
})
