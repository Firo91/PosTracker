release: python manage.py migrate
web: gunicorn netwatch.wsgi:application --log-file -
worker: celery -A netwatch worker -l info
beat: celery -A netwatch beat -l info
