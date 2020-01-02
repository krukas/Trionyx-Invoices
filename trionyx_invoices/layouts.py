"""
trionyx_invoices.layouts
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from trionyx.views import tabs
from trionyx.layout import Container, Row, Column8, Column4, Panel, DescriptionList, Html, Table, Link
from django.utils.translation import ugettext_lazy as _

from .models import Invoice, InvoiceItem


@tabs.register(Invoice)
def invoice_general(obj):
    from .apps import render_status
    hourly_items = obj.items.filter(type=InvoiceItem.TYPE_HOURLY_RATE)
    price_items = obj.items.filter(type=InvoiceItem.TYPE_PRICE)
    return Container(
        Row(
            Column4(
                Panel(
                    _('Info'),
                    DescriptionList(
                        'reference',
                        {
                            'field': 'status',
                            'renderer': lambda value, data_object, **options: render_status(data_object),
                        },
                        {
                            'label': _('For'),
                            'value': Link(object=obj.for_object, lock_object=True),
                        } if obj.for_object_id else False,
                        'send_date',
                        'due_date',
                    ),
                )
            ),
            Column4(
                Panel(
                    _('Invoiced to'),
                    DescriptionList(
                        'billing_company_name',
                        'billing_name',
                        'billing_email',
                        'billing_telephone',
                    )
                )
            ),
            Column4(
                Panel(
                    _('Billing address'),
                    DescriptionList(
                        'billing_address',
                        'billing_postcode',
                        'billing_city',
                        'billing_country',
                    )
                )
            )
        ),
        Row(
            Column8(
                Panel(
                    _('Hourly items'),
                    Table(
                        hourly_items,
                        'description',
                        'hourly_rate=width:100px',
                        'hours=width:100px',
                        'row_total=width:100px',
                    ),
                ) if hourly_items else False,
                Panel(
                    _('Price items'),
                    Table(
                        price_items,
                        'description',
                        'price=width:100px',
                        'qty=width:100px',
                        'row_total=width:100px',
                    ),
                ) if price_items else False,
            ),
            Column4(
                Panel(
                    _('Totals'),
                    DescriptionList(
                        'subtotal',
                        'discount_total',
                        'tax_total',
                        'grand_total',
                    )
                ),
                Panel(
                    _('Comment'),
                    Html(obj.comment),
                    collapse = False
                ),
            )
        )
    )