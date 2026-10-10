"""
WSGI Entrypoint for Production Deployment.
Compatible with Gunicorn, Waitress, uWSGI, AWS Elastic Beanstalk, Docker, and Render/Railway.
"""
import os
import config
from app import app

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# WSGI standard callable
application = app

if __name__ == "__main__":
    try:
        import waitress
        print(f"[*] Starting Waitress production server on http://{config.HOST}:{config.PORT}")
        waitress.serve(app, host=config.HOST, port=config.PORT, threads=6)
    except ImportError:
        print(f"[*] Running development server on http://{config.HOST}:{config.PORT}")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
