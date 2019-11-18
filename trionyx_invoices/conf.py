from django.conf import settings
from trionyx.config import AppSettings

settings = AppSettings('INVOICES', {
    'REFERENCE_FORMAT': '{increment_long}',
    'PAYMENT_INSTRUCTIONS': '',
    'PDF_FOOTER': '',
    'PDF_COLOR': settings.TX_THEME_COLOR.replace('-light', ''),
})