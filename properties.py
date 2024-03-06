from main_properties import CELERY_SERVER
import os
from celery.schedules import crontab


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_DIR = 'ssl_monitoring'

#celery and redis config
CELERY_BROKER = 'redis://{}/0'.format(CELERY_SERVER)
CELERY_BACKEND = CELERY_BROKER
CELERY_QUEUE = "{}Queue".format(MAIN_DIR)
CELERY_CONCURRENCY = 6
CELERY_HOSTNAME = "{}Hostname".format(MAIN_DIR)



# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'vhchong@snsoft.my'
EMAIL_HOST_PASSWORD = 'Snsoft@2024'