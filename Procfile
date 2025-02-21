web: cd SIT && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn SIT.wsgi:application --bind 0.0.0.0:$PORT
