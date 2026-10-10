import os
from pathlib import Path

# Load .env file automatically if present
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

# Environment and Debug mode
ENV = os.environ.get("FLASK_ENV", os.environ.get("ENV", "production"))
DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

# Database configuration
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "qr_maintenance_db")
MYSQL_POOL_SIZE = int(os.environ.get("MYSQL_POOL_SIZE", "10"))

# Remote Cloud Database SSL settings (e.g. TiDB Serverless, Aiven, Clever Cloud)
MYSQL_SSL_DISABLED = os.environ.get(
    "MYSQL_SSL_DISABLED",
    "1" if MYSQL_HOST in ("127.0.0.1", "localhost", "db") else "0"
).lower() in ("1", "true", "yes")
MYSQL_SSL_CA = os.environ.get("MYSQL_SSL_CA", "")

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "qr_maintenance_super_secret_key_change_me")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")

# Reverse proxy support (e.g. Nginx, Cloudflare, AWS ALB)
BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "0").lower() in ("1", "true", "yes")
PROXY_FIX_NUM_PROXIES = int(os.environ.get("PROXY_FIX_NUM_PROXIES", "1"))

# Server bind settings
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# Upload settings
UPLOAD_FOLDER = os.environ.get(
    "UPLOAD_FOLDER",
    os.path.join(os.path.dirname(__file__), "uploads")
)
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 8 * 1024 * 1024))

# Public URL phones use when opening QR codes (no trailing slash).
# Example: http://192.168.1.10:5000 or https://maintenance.school.edu
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")

