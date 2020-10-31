"""
trionyx_accounts.apps
~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from trionyx.trionyx.apps import BaseConfig
from trionyx.config import ModelConfig
from django.utils.translation import ugettext_lazy as _


def render_status(model, *args, **kwargs):
    """Render status as label"""
    mapping = {
        10: 'default',
        20: 'info',
        30: 'warning',
        40: 'success',
        99: 'danger',
    }

    return '<span class="label label-{}">{}</span>'.format(
        mapping.get(model.status, 'default'),
        model.get_status_display()
    )


def get_publish_url(obj, context):
    """Get publish url"""
    from trionyx.urls import model_url
    return model_url(obj, 'dialog-edit', code='publish')


def get_complete_url(obj, context):
    """Get publish url"""
    from trionyx.urls import model_url
    return model_url(obj, 'dialog-edit', code='complete')


class InvoicesConfig(BaseConfig):
    """Django core config app"""

    name = 'trionyx_invoices'
    verbose_name = _('Invoices')

    class Invoice(ModelConfig):
        menu_root = True
        menu_icon = 'fa fa-file-text-o'
        menu_order = 80
        verbose_name = '{reference}'

        list_default_fields = [
            'created_at',
            'due_date',
            'billing_company_name',
            'reference',
            'status',
            'grand_total',
        ]

        list_fields = [
            {
                'field': 'status',
                'renderer': render_status
            }
        ]

        display_delete_button = False
        display_change_button = False

        header_buttons = [
            {
                'label': _('Delete'),
                'url': 'trionyx:model-dialog-delete',
                'dialog': True,
                'show': lambda obj, context: obj and obj.status == 10,
                'dialog_options': {
                    'callback': """function(data, dialog){
                        if (data.success) {
                            dialog.close();
                            window.location.href = '/model/trionyx_invoices/invoice/';
                        }
                    }"""
                }
            },
            {
                'label': _('Publish'),
                'url': get_publish_url,
                'type': 'btn-info',
                'show': lambda obj, context: obj and obj.pk and obj.status == 10 and obj.items.count(),
                'dialog_options': {
                    'callback': """function(data, dialog){
                        if (data.success) {
                            window.location.href = String(dialog.url).replace(/^\/dialog|edit\/publish\/$/g, '');
                            dialog.close();
                        }
                    }"""  # noqa: W605
                }
            },
            {
                'label': _('PDF'),
                'url': lambda obj, context: obj.pdf.url if obj.pdf else '',
                'show': lambda obj, context: obj and obj.pk and obj.status in [20, 30, 40] and context.get('tab') == 'general',
                'dialog': False,
                'target': '_blank',
            },
            {
                'label': _('Complete'),
                'url': get_complete_url,
                'type': 'btn-success',
                'show': lambda obj, context: obj and obj.pk and obj.status in [20, 30] and context.get('tab') == 'general',
                'dialog_options': {
                    'callback': """function(data, dialog){
                        if (data.success) {
                            trionyx_reload_tab('general');
                            dialog.close();
                        }
                    }"""
                }
            },
        ]

    class InvoiceType(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True

    class InvoiceItem(ModelConfig):
        menu_exclude = True
        disable_search_index = True

    class InvoiceComment(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True

    class InvoicePage(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True
