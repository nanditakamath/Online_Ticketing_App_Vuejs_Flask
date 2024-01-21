import os

from celery.schedules import crontab


broker_url = os.environ.get('BROKER_URL', "redis://localhost:6379/1")
result_backend = os.environ.get('RESULT_BACKEND', "redis://localhost:6379/2")
broker_connection_return_on_startup = True

imports = ('jobs.report_html','hello')

beat_schedule = {
    'send-reminder': {
        'task': 'send_reminder',
        'schedule': crontab(minute='*')
    },
    'monthly-report': {
        'task': 'jobs.report_html.send_reports_to_users',
        'schedule': crontab(minute='*')
    },
    'hello_test':{
        'task': 'hello.hello',
        'schedule': crontab(minute='*')
    }
}