import os
from openedx.core.lib.derived import derive_settings
from .common import *


STATIC_ROOT = os.environ.get('STATIC_ROOT')

# hacks to overcome edx habbit to create objects in import time
DATABASES = {
    'default': {'ENGINE': None}
}

XQUEUE_INTERFACE = {
    'url': None,
    'django_auth': None
}

LOCALE_PATHS = os.environ.get('LOCALE_PATHS').split(';')
derive_settings(__name__)
