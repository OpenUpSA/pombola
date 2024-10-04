web: gunicorn --workers 3 --worker-class gevent --timeout 30 --max-requests 10000 --max-requests-jitter 100 --limit-request-line 7168 --log-file - -b 0.0.0.0:5000 pombola.wsgi:application
worker: celery -A pombola worker
beat: celery -A pombola beat --pidfile= -s /var/celerybeat/celerybeat-schedule
