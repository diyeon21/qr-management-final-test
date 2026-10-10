web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --keep-alive 5 --timeout 120
release: python init_db.py --seed
