# This Python file uses the following encoding: utf-8

from .base import *

# Additional locations of static files
STATICFILES_DIRS = (
    "C:/Users/grabsch/wspdev/wspSite/wsp_frontend/static/",
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_DIRS = (
    "C:/Users/grabsch/wspdev/wspSite/wsp_frontend/templates",
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# Logging preferences
# Because splitting the logging configuration into base.py and 
# local.py/production.py does not work, the configuration here is basically
# the same as for the production settings (production.py). Only the log file 
# path is different.
#
# IMPORTANT: Every change here needs to be repeated in production.py!

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'standard_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024*1024*5, # equals 5MB
            'backupCount': 5,
            'formatter': 'standard',
            'filename': 'site.log',
        },
        'request_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024*1024*5, # equals 5MB
            'backupCount': 5,
            'formatter': 'standard',
            'filename': 'requests.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['standard_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False, # do not propagate HTTP requests to the 
                                # standard logger
        },
        'requests': {
            'level': 'WARNING'
        },
    }
}