@echo off
echo Starting Production Server with Waitress WSGI...
echo Listening on http://0.0.0.0:5000
echo Press CTRL+C to stop.
python -m waitress --listen=0.0.0.0:5000 wsgi:app
pause
