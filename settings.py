import os

from trionyx.settings import *

INTERNAL_IPS = ('127.0.0.1','::1', '0.0.0.0')

INSTALLED_APPS += [
    # Development apps
    'django_extensions',
    'debug_toolbar',
]

MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + list(MIDDLEWARE)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOCALE_PATHS = (
	os.path.join(BASE_DIR, 'trionyx_invoices', 'locale'),
)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

COMPRESS_ENABLED = False

TX_COMPANY_NAME = 'Trionyx'
TX_COMPANY_ADDRESS_LINES = [
	'Street 123',
	'1234AB, City',
]
TX_COMPANY_TELEPHONE = '+123456789'
TX_COMPANY_WEBSITE = 'https://djangoproject.com'
TX_COMPANY_EMAIL = 'info@djangoproject.com'


INVOICES_PAYMENT_INSTRUCTIONS = """
<strong>IBAN: EU01 ABCD 0000 0000 01</strong><br/>
<br/>
Please include the invoice number on your transaction
"""
INVOICES_PDF_FOOTER = 'VAT: 1234567890'
INVOICES_PDF_COLOR = 'green'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'development.sqlite3'),
    }
}

# Celery beat schedule
from trionyx.utils import create_celerybeat_schedule
CELERY_BEAT_SCHEDULE = create_celerybeat_schedule(INSTALLED_APPS)

LOGGING = {
	'version': 1,
	'formatters': {
		'color_console': {
			'()': 'colorlog.ColoredFormatter',
			'format': '%(log_color)s%(levelname)-8s [%(name)s:%(lineno)s]%(reset)s %(blue)s %(message)s',
			'datefmt': "%d/%b/%Y %H:%M:%S",
			'log_colors': {
				'DEBUG': 'cyan',
				'INFO': 'green',
				'WARNING': 'yellow',
				'ERROR': 'red',
				'CRITICAL': 'red',
			},
		},
	},
	'filters': {
		'require_debug_true': {
			'()': 'django.utils.log.RequireDebugTrue',
		}
	},
	'handlers': {
		'console': {
			'level': 'DEBUG',
			'filters': ['require_debug_true'],
			'class': 'logging.StreamHandler',
			'formatter': 'color_console',
		}
	},
	'loggers': {
		'apps': {
			'level': 'DEBUG',
			'handlers': ['console'],
		},
        'trionyx': {
			'level': 'DEBUG',
			'handlers': ['console'],
		},
        'django_jsend': {
			'level': 'DEBUG',
			'handlers': ['console'],
		},
		# 'django.db.backends': {
		#     'level': 'DEBUG',
		#     'handlers': ['console'],
		# },
		'werkzeug': {
			'handlers': ['console'],
			'level': 'DEBUG',
			'propagate': True,
		},
	}
}