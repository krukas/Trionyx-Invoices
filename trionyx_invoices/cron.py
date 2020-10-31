from celery.schedules import crontab


schedule = {
    'invoice-overdue': {
        'task': 'trionyx_invoices.tasks.mark_overdue_invoices',
        'schedule': crontab(hour=3, minute=0)
    },
    'invoice-reminders': {
        'task': 'trionyx_invoices.tasks.send_reminders',
        'schedule': crontab(hour=9, minute=0)
    },
    'invoice-past-dues': {
        'task': 'trionyx_invoices.tasks.send_past_dues',
        'schedule': crontab(hour=9, minute=0)
    },
}
