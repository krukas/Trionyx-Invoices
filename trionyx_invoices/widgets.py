from trionyx.widgets import BaseWidget
from trionyx.renderer import renderer

from .models import Invoice


class OpenInvoicesWidget(BaseWidget):
    code = 'open_invoices'
    name = 'Open Invoices'
    description = 'Shows open invoices'

    def get_data(self, request, config):
        from .apps import render_status
        return [
            {
                'due_date': renderer.render_field(invoice, 'due_date'),
                'reference': renderer.render_field(invoice, 'reference'),
                'status': render_status(invoice),
                'billing_company_name': renderer.render_field(invoice, 'billing_company_name'),
                'grand_total': renderer.render_field(invoice, 'grand_total'),
                'url': invoice.get_absolute_url(),
            } for invoice in Invoice.objects.filter(
                status__in=[Invoice.STATUS_SEND, Invoice.STATUS_OVERDUE]
            ).order_by('due_date')
        ]
