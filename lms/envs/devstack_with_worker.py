"""
This config file follows the devstack enviroment, but adds the
requirement of a celery worker running in the background to process
celery tasks.

When testing locally, run lms/cms with this settings file as well, to test queueing
of tasks onto the appropriate workers.

In two separate processes on devstack:
    paver devstack lms --settings=devstack_with_worker
    ./manage.py lms celery worker --settings=devstack_with_worker
For periodic task to start add -B key:
    ./manage.py lms celery worker -B --settings=devstack_with_worker
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import
from lms.envs.devstack import *

# Require a separate celery worker
CELERY_ALWAYS_EAGER = False

# Periodic tasks can be created automatically at project start (when celery process is started).
# To not create them manually in admin (but they still will be shown in admin),
# we can define them in settings.py in such way.
CELERYBEAT_SCHEDULE = {
    'student_counter': {
    'task': 'openedx.core.djangoapps.global_statistics.tasks.count_data',
    'schedule': 20,
    }
}

# URL to send data within periodic task processing.
PERIODIC_TASK_POST_URL = 'http://192.168.1.139:7000/receive/'

# Geographical coordinates of the eDX platform server location in decimal degrees up to the city.
# Please use these settings if your eDX server's location differ from its physical location.
# For example, you use cloud services like Amazon(AWS), Microsoft(Azure), etc.
# Otherwise, leave these settings as is.

# Example of usage: 'Europe/Kiev' PLATFORM_LATITUDE = '50.4546600', PLATFORM_LONGITUDE = '30.5238000'

PLATFORM_LATITUDE = ''
PLATFORM_LONGITUDE = ''

# Disable transaction management because we are using a worker. Views
# that request a task and wait for the result will deadlock otherwise.
for database_name in DATABASES:
    DATABASES[database_name]['ATOMIC_REQUESTS'] = False
