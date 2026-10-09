import os
from urllib.parse import urlparse

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

database_url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL")
if database_url:
    parsed = urlparse(database_url)
    MYSQL_HOST = parsed.hostname or "127.0.0.1"
    MYSQL_PORT = parsed.port or 3306
    MYSQL_USER = parsed.username or "root"
    MYSQL_PASSWORD = parsed.password or ""
    MYSQL_DB = (parsed.path or "/qr_maintenance_db").lstrip("/")
else:
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "qr_maintenance_db")

SECRET_KEY = os.environ.get("SECRET_KEY", "qr_maintenance_super_secret_key_change_me")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads"))
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 8 * 1024 * 1024))

# Public URL used in QR codes (e.g., https://yourdomain.com or http://192.168.1.5:5000)
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")

# Debug flag (default False in production)
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
