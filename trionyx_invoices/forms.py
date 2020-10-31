"""
trionyx_invoices.forms
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from trionyx import forms
from trionyx.forms.helper import FormHelper
from trionyx.forms.layout import Layout, Fieldset, Div, InlineForm, Field, HTML, Depend
from django.apps import apps
from django.forms.models import inlineformset_factory
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .models import Invoice, InvoiceItem
from .tasks import InvoicePublishTask
from .conf import settings


class InvoiceItemPriceForm(forms.ModelForm):
    description = forms.CharField()
    qty = forms.IntegerField(initial=1)

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
    hourly_rate = forms.DecimalField(initial=settings.HOURLY_PRICE)
    hours = forms.DecimalField(initial=1)

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

        billing_row = Div(
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
        )

        if apps.is_installed("trionyx_accounts") and not self.instance.id:
            from trionyx_accounts.models import Account
            self.fields['account'] = forms.ChoiceField(
                label=_('Account'),
                choices=[
                    ('', '-----'),
                    ('__custom__', _('Custom')),
                    *Account.objects.values_list('id', 'verbose_name')
                ],
                required=True,
                initial=self.instance.for_object_id,
            )
            billing_row = Div(
                'account',
                Depend(
                    [('account', r'__custom__')],
                    billing_row,
                )
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            billing_row,
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

    def save(self, commit=True):
        is_new = not self.instance.id
        invoice = super().save(commit)

        if is_new and apps.is_installed("trionyx_accounts") and self.cleaned_data['account'] != '__custom__':
            from trionyx_accounts.models import Account
            account = Account.objects.get(id=self.cleaned_data['account'])
            invoice.for_object = account
            invoice.billing_company_name = account.name
            invoice.billing_email = account.email
            invoice.billing_telephone = account.phone

            if account.billing_address:
                invoice.billing_address = account.billing_address.street
                invoice.billing_city = account.billing_address.city
                invoice.billing_postcode = account.billing_address.postcode
                invoice.billing_country = account.billing_address.country

            invoice.save()

        return invoice


@forms.register(code='publish')
class PublishInvoice(forms.ModelForm):
    """Publish invoice form"""

    days = forms.IntegerField(label=_('Invoice due in days'), required=True, initial=30)
    status = forms.CharField(widget=forms.HiddenInput(), required=False)
    due_date = forms.DateTimeField(widget=forms.HiddenInput(), required=False)

    class Meta:
        """Form meta"""

        model = Invoice
        fields = ['days', 'due_date', 'status']

    def __init__(self, *args, **kwargs):
        """Init form"""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'days',
            Field('status', hidden=True),
            Field('due_date', hidden=True)
        )

    def clean_due_date(self):
        return timezone.now() + timezone.timedelta(days=self.cleaned_data['days'])

    def clean_status(self):
        return Invoice.STATUS_SEND

    def get_title(self):
        """Get title"""
        return _('Publish and send invoice to customer')

    def get_submit_label(self):
        """Get submit label"""
        return _('Publish')

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        InvoicePublishTask().delay(
            task_object=obj,
            task_description=_(f'Publishing invoice #{obj.reference}')
        )
        return obj


@forms.register(code='complete')
class CompleteInvoice(forms.ModelForm):
    """Paid invoice form"""

    status = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        """Form meta"""

        model = Invoice
        fields = ['status']

    def __init__(self, *args, **kwargs):
        """Init form"""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('status', hidden=True),
            HTML(_('Mark invoice as paid')),
        )

    def clean_status(self):
        return Invoice.STATUS_PAID

    def get_title(self):
        """Get title"""
        return _('Complete invoice')

    def get_submit_label(self):
        """Get submit label"""
        return _('Completed')
