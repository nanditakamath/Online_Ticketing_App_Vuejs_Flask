import os

config = {
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///test.db'),
    'SECRET_KEY': '$12345$',
    'CELERY': {
        'broker_url': 'redis:///',
        'result_backend': 'redis:///' 
    }    
}