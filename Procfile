web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120
release: python init_db.py --seed
