import os

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "qr_maintenance_db")
SECRET_KEY  = os.environ.get("SECRET_KEY",  "qr_maintenance_super_secret_key_change_me")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
MAX_CONTENT_LENGTH = 8 * 1024 * 1024

# Public URL phones use when opening QR codes (no trailing slash).
# Example: http://192.168.1.10:5000 — set this if QRs still show localhost.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
