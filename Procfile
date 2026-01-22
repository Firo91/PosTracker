release: sh -c "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py create_initial_admin"
web: gunicorn netwatch.wsgi:application --log-file -
worker: celery -A netwatch worker -l info
beat: celery -A netwatch beat -l info
