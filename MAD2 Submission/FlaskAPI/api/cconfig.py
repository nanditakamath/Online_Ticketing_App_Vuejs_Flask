import os

from celery.schedules import crontab


broker_url = os.environ.get('BROKER_URL', "redis://localhost:6379/1")
result_backend = os.environ.get('RESULT_BACKEND', "redis://localhost:6379/2")
broker_connection_return_on_startup = True

imports = ('hello')

beat_schedule = {
    'hello_test':{
        'task': 'hello.hello',
        'schedule': crontab(minute='*')
    },
    'monthly-report': {
        'task': 'hello.send_reports_to_users',
        'schedule': crontab(minute='*')
    },
    'reminder-email': {
        'task': 'hello.send_reminder_emails',
        'schedule': crontab(minute='*') 
    }
}


