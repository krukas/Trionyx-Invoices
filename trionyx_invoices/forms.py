"""
trionyx_invoices.forms
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from trionyx import forms
from trionyx.forms.helper import FormHelper
from trionyx.forms.layout import Layout, Fieldset, Div, InlineForm
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from .models import Invoice, InvoiceItem


class InvoiceItemPriceForm(forms.ModelForm):
    description = forms.CharField()

    def __init__(self, *args, **kwargs):
        """Init user form"""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta:
        model = InvoiceItem
        fields = ['description', 'price', 'qty']

    def save(self, commit=True):
        item = super().save(False)
        item.type = InvoiceItem.TYPE_PRICE

        if commit:
            item.save()

        return item

InvoiceItemPriceFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemPriceForm, can_delete=True, extra=0
)

class InvoiceItemHourlyForm(forms.ModelForm):
    description = forms.CharField()

    def __init__(self, *args, **kwargs):
        """Init user form"""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta:
        model = InvoiceItem
        fields = ['description', 'hourly_rate', 'hours']

    def save(self, commit=True):
        item = super().save(False)
        item.type = InvoiceItem.TYPE_HOURLY_RATE

        if commit:
            item.save()

        return item

InvoiceItemHourlyFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemHourlyForm, can_delete=True, extra=0
)

@forms.register(default_create=True, default_edit=True)
class InvoiceForm(forms.ModelForm):
    comment = forms.Wysiwyg(required=False)

    inline_forms = {
        'items_hourly': {
            'form': InvoiceItemHourlyFormSet,
            'queryset': InvoiceItem.objects.filter(type=InvoiceItem.TYPE_HOURLY_RATE)
        },
        'items_price': {
            'form': InvoiceItemPriceFormSet,
            'queryset': InvoiceItem.objects.filter(type=InvoiceItem.TYPE_PRICE)
        }
    }

    class Meta:
        """Form meta"""

        model = Invoice
        fields = [
            'billing_company_name', 'billing_name', 'billing_email', 'billing_telephone',
            'billing_address', 'billing_postcode', 'billing_city', 'billing_country',
            'discount_total', 'comment',
        ]

    def __init__(self, *args, **kwargs):
        """Init form"""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    _('Invoiced to'),
                    Div(
                        'billing_company_name',
                        css_class='col-md-6'
                    ),
                    Div(
                        'billing_name',
                        css_class='col-md-6'
                    ),
                    Div(
                        'billing_email',
                        css_class='col-md-6'
                    ),
                    Div(
                        'billing_telephone',
                        css_class='col-md-6'
                    ),
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Billing address'),
                    Div(
                        'billing_address',
                        css_class='col-md-12'
                    ),
                    Div(
                        'billing_postcode',
                        css_class='col-md-2'
                    ),
                    Div(
                        'billing_city',
                        css_class='col-md-6'
                    ),
                    Div(
                        'billing_country',
                        css_class='col-md-4'
                    ),
                    css_class='col-md-6'
                ),
                css_class='row',
            ),
            Div(
                Div(
                    Fieldset(
                        _('Hourly items'),
                        InlineForm('items_hourly'),
                    ),
                    Fieldset(
                        _('Price items'),
                        InlineForm('items_price'),
                    ),
                    css_class='col-md-8'
                ),
                Div(
                    'discount_total',
                    'comment',
                    css_class='col-md-4'
                ),
                css_class='row'
            ),

        )