import logging
from decimal import Decimal

from trionyx import models
from trionyx.data import COUNTRIES
from trionyx.config import variables
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import fields
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from weasyprint import HTML, CSS

from .conf import settings as app_settings

logger = logging.getLogger(__name__)


def pdf_upload_path(instance, filename):
    """Generate upload path"""
    return f'invoices/{instance.reference}.pdf'


class InvoiceType(models.BaseModel):
    """Account type model"""

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        """Model meta"""

        verbose_name = _('Invoice type')
        verbose_name_plural = _('Invoice types')


class Invoice(models.BaseModel):
    STATUS_DRAFT = 10
    STATUS_SEND = 20
    STATUS_OVERDUE = 30
    STATUS_PAID = 40
    STATUS_CANCELED = 99

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_SEND, _('Send')),
        (STATUS_OVERDUE, _('Overdue')),
        (STATUS_PAID, _('Paid')),
        (STATUS_CANCELED, _('Canceled')),
    ]

    STATUS_FLOWS = {
        STATUS_DRAFT: [STATUS_SEND],
        STATUS_SEND: [STATUS_OVERDUE, STATUS_PAID, STATUS_CANCELED],
        STATUS_PAID: [],
        STATUS_OVERDUE: [STATUS_CANCELED, STATUS_PAID],
        STATUS_CANCELED: [],
    }

    type = models.ForeignKey(InvoiceType, models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_('Type'))

    # Connect Invoice to other Model
    for_object_type = models.ForeignKey(
        'contenttypes.ContentType',
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Object type'),
    )
    for_object_id = models.BigIntegerField(_('Object ID'), blank=True, null=True)
    for_object = fields.GenericForeignKey('for_object_type', 'for_object_id')

    auto_generate_id = models.CharField(max_length=32, null=True, blank=True)
    """Unique id used for generating the Invoice, that later can be used to update the same order"""

    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_DRAFT)
    reference = models.CharField(_('Reference'), max_length=32, blank=True, null=True)
    due_date = models.DateField(_('Due date'), null=True, blank=True)

    send_date = models.DateField(_('Send on'), null=True, blank=True)
    send_reminder_date = models.DateField(_('Reminder send on'), null=True, blank=True)
    send_past_due_date = models.DateField(_('Past due send on'), null=True, blank=True)

    discount_total = models.PriceField(_('Discount total'), default=0.0, blank=True)
    subtotal = models.PriceField(_('Subtotal'), default=0.0, blank=True)
    tax_percentage = models.PositiveIntegerField(_('Tax percentage'), null=True, blank=True)
    tax_total = models.PriceField(_('Tax total'), default=0.0, blank=True)
    grand_total = models.PriceField(_('Grand total'), default=0.0, blank=True)

    pdf = models.FileField(upload_to=pdf_upload_path, blank=True, null=True, default=None)

    comment = models.TextField(_('Comment'), null=True, blank=True)

    # Billing information
    billing_name = models.CharField(_('Billing name'), max_length=128, null=True, blank=True)
    billing_company_name = models.CharField(_('Billing company name'), max_length=128, null=True, blank=True)
    billing_email = models.EmailField(_('Billing email'), null=True, blank=True)
    billing_telephone = models.CharField(_('Billing telephone'), max_length=32, null=True, blank=True)
    billing_address = models.CharField(_('Billing address'), max_length=128, null=True, blank=True)
    billing_postcode = models.CharField(_('Billing postcode'), max_length=16, null=True, blank=True)
    billing_city = models.CharField(_('Billing city'), max_length=256, null=True, blank=True)
    billing_country = models.CharField(_('Billing country'), max_length=2, choices=COUNTRIES, blank=True, null=True)

    class Meta:
        """Model meta"""

        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_status = self.status

    @property
    def address_lines(self):
        return filter(None, [
            self.billing_name,
            self.billing_company_name,
            self.billing_address,
            ', '.join(filter(None, [self.billing_postcode, self.billing_city, self.get_billing_country_display()]))
        ])

    @property
    def subtotal_incl_tax(self):
        return self.subtotal + self.tax_total

    @property
    def negative_discount(self):
        return - self.discount_total

    def collect_totals(self):
        """Collect totals"""
        self.discount_total = Decimal(self.discount_total) if self.discount_total is not None else Decimal()
        self.tax_percentage = int(self.tax_percentage) if self.tax_percentage is not None else Decimal()

        results = self.items.aggregate(
            row_total=models.Sum('row_total'),
        )
        self.subtotal = Decimal(results['row_total']) if results['row_total'] else Decimal()
        self.tax_total = self.subtotal * Decimal(self.tax_percentage / 100)
        self.grand_total = (self.subtotal - self.discount_total) + self.tax_total

    def create_pdf(self):
        """Create invoice PDF"""
        colors = {
            'blue': {
                'normal': '#3c8dbc',
                'darker': '#357ca5',
            },
            'yellow': {
                'normal': '#f39c12',
                'darker': '#db8b0b',
            },
            'green': {
                'normal': '#00a65a',
                'darker': '#008d4c',
            },
            'purple': {
                'normal': '#605ca8',
                'darker': '#555299',
            },
            'red': {
                'normal': '#dd4b39',
                'darker': '#d33724',
            },
            'black': {
                'normal': '#111111',
                'darker': '#000000',
            },
        }

        theme = app_settings.PDF_COLOR
        theme = theme if theme in colors else 'black'

        html = HTML(string=render_to_string('invoices/pdf/invoice.html', {
            'invoice': self,
            'payment_instructions': app_settings.PAYMENT_INSTRUCTIONS,
            'hourly_items': self.items.filter(type=InvoiceItem.TYPE_HOURLY_RATE).order_by('order'),
            'price_items': self.items.filter(type=InvoiceItem.TYPE_PRICE).order_by('order'),
            'company': {
                'name': settings.TX_COMPANY_NAME,
                'address_lines': settings.TX_COMPANY_ADDRESS_LINES,
                'telephone': settings.TX_COMPANY_TELEPHONE,
                'website': settings.TX_COMPANY_WEBSITE,
                'email': settings.TX_COMPANY_EMAIL,
            },
            'footer': app_settings.PDF_FOOTER,
        }))

        if self.pdf:
            self.pdf.delete()

        self.pdf.save(
            f'{self.reference}.pdf',
            ContentFile(html.write_pdf(
                stylesheets=[CSS(string=render_to_string('invoices/pdf/invoice.css.html', {
                    'colors': colors[theme],
                }))]
            ))
        )

    def save(self, *args, **kwargs):
        # Check if valid status update
        if self.__original_status != self.status and self.status not in self.STATUS_FLOWS[self.__original_status]:
            raise ValidationError('Invalid status change, valid statuses are {}'.format(
                ', '.join(str(x) for x in self.STATUS_FLOWS[self.__original_status])
            ))

        if self.status != self.STATUS_DRAFT and self.items.count() == 0:
            raise ValidationError("Cant't publish a invoice without items")

        if self.__original_status == self.STATUS_DRAFT:
            self.collect_totals()

        if not self.reference:
            with variables.get_increment('invoices_invoice_increment') as increment:
                self.reference = app_settings.REFERENCE_FORMAT.format(
                    increment=increment,
                    increment_long=str(increment).zfill(8),
                )
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


    def get_absolute_url(self):
        """Get absolute url, in Draft returns edit form"""
        if self.status == self.STATUS_DRAFT:
            from trionyx.urls import model_url
            return model_url(self, 'edit')
        return super().get_absolute_url()

    # Need to add signal hook to disable edit/delete after invoice is published
    # - Add signals for disable_(add/edit/delete)


class InvoiceItem(models.BaseModel):
    TYPE_HOURLY_RATE = 10
    TYPE_PRICE = 20

    TYPE_CHOICES = [
        (TYPE_HOURLY_RATE, _('Hourly rate')),
        (TYPE_PRICE, _('Price')),
    ]

    invoice = models.ForeignKey(Invoice, models.CASCADE, related_name='items', verbose_name=_('Invoice'))
    type = models.IntegerField(_('Type'), choices=TYPE_CHOICES)

    auto_generate_id = models.CharField(max_length=32, null=True, blank=True)
    """Unique id used for generating the InvoiceItem, that later can be used to update the same InvoiceItem"""

    reference = models.CharField(_('Reference'), max_length=32, null=True, blank=True)
    description = models.TextField(_('Description'), null=True, blank=True)
    order = models.PositiveIntegerField(_('Order'), null=True, blank=True)

    hourly_rate = models.PriceField(_('Hourly rate'), default=0.0, blank=True)
    hours = models.DecimalField(_('Hours'), max_digits=19, decimal_places=2, default=0.0, blank=True)

    price = models.PriceField(_('Price'), default=0.0, blank=True)
    qty = models.PositiveIntegerField(_('Qty'), default=0.0, blank=True)

    row_total = models.PriceField(_('Row total'), default=0.0, blank=True)

    class Meta:
        """Model meta"""

        verbose_name = _('Item')
        verbose_name_plural = _('Items')

    def collect_totals(self):
        """Collect item totals"""
        self.price = Decimal(self.price if self.price else 0.0)
        self.qty = Decimal(self.qty if self.qty else 0)
        self.hourly_rate = Decimal(self.hourly_rate if self.hourly_rate else 0.0)
        self.hours = Decimal(self.hours if self.hours else 0.0)

        if self.type == self.TYPE_PRICE:
            self.row_total = self.price * self.qty
        else:
            self.row_total = self.hourly_rate * self.hours

    def save(self, *args, **kwargs):
        self.collect_totals()

        super().save(*args, **kwargs)

        if not self._state.adding:
            try:
                self.invoice.collect_totals()
                self.invoice.save()
            except Exception as e:
                logger.exception(e)


class InvoiceComment(models.BaseModel):
    invoice = models.ForeignKey(Invoice, models.CASCADE, related_name='comments', verbose_name=_('Invoice'))
    is_public = models.BooleanField(_('Is public'), default=False, blank=True)
    is_send = models.BooleanField(_('Is send'), default=False, blank=True)
    comment = models.TextField(_('Comment'))

    class Meta:
        """Model meta"""

        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')