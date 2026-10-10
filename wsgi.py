import os
import config
from app import app

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

application = app

if __name__ == "__main__":
    try:
        import waitress
        print(f"Server running on http://{config.HOST}:{config.PORT}")
        waitress.serve(app, host=config.HOST, port=config.PORT, threads=8, channel_timeout=30, cleanup_interval=30)
    except ImportError:
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
