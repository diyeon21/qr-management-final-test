import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import mysql.connector
from mysql.connector import pooling
import config

_pool = None
_initialized = False


def get_db():
    global _pool, _initialized
    if _pool is None:
        try:
            bootstrap = mysql.connector.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
            )
            bcur = bootstrap.cursor()
            bcur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB}`")
            bootstrap.commit()
            bcur.close()
            bootstrap.close()
        except Exception:
            # Cloud hosts (e.g. Railway, Render, Supabase) may restrict CREATE DATABASE or the db already exists
            pass

        _pool = pooling.MySQLConnectionPool(
            pool_name="webbased_pool",
            pool_size=8,
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB,
            autocommit=False,
        )

    cnx = _pool.get_connection()
    if not _initialized:
        cur = cnx.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                email       VARCHAR(255) NOT NULL UNIQUE,
                password    VARCHAR(255) NOT NULL,
                role        ENUM('admin','custodian','technician','faculty') NOT NULL DEFAULT 'faculty',
                created_at  DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin','custodian','technician','faculty') NOT NULL DEFAULT 'faculty'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted TINYINT(1) NOT NULL DEFAULT 0")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                name              VARCHAR(255) NOT NULL,
                category          VARCHAR(255),
                location          VARCHAR(255),
                purchase_cost     DECIMAL(12,2) DEFAULT 0,
                maintenance_cost  DECIMAL(12,2) DEFAULT 0,
                status            VARCHAR(64) DEFAULT 'Working',
                qr_code           TEXT,
                created_at        DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("ALTER TABLE equipment ADD COLUMN IF NOT EXISTS is_deleted TINYINT(1) NOT NULL DEFAULT 0")
        cur.execute("ALTER TABLE equipment ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_requests (
                id                  INT AUTO_INCREMENT PRIMARY KEY,
                equipment_id        INT NOT NULL,
                reported_by         INT NOT NULL,
                description         TEXT,
                urgency             VARCHAR(64) DEFAULT 'Medium',
                image               VARCHAR(512),
                status              VARCHAR(64) DEFAULT 'Pending',
                affected_component  VARCHAR(100) NULL,
                date_reported       DATETIME NOT NULL,
                date_responded      DATETIME,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (reported_by)  REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS technician_id INT NULL")
        try:
            cur.execute("ALTER TABLE maintenance_requests ADD CONSTRAINT fk_technician FOREIGN KEY (technician_id) REFERENCES users(id) ON DELETE SET NULL")
        except Exception:
            pass  # Constraint may already exist
        cur.execute("ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL")
        cur.execute("ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS affected_component VARCHAR(100) NULL")
        cur.execute("ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS repair_start DATETIME NULL")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                equipment_id    INT NOT NULL,
                request_id      INT NOT NULL,
                cost            DECIMAL(12,2) DEFAULT 0,
                action_taken    TEXT,
                date_completed  DATETIME NOT NULL,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (request_id)   REFERENCES maintenance_requests(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS repair_start DATETIME NULL")
        cur.execute("ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS duration_minutes INT NULL")
        cur.execute("ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS technician_id INT NULL")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                actor_id      INT,
                action        VARCHAR(255) NOT NULL,
                details       TEXT,
                target_type   VARCHAR(100),
                target_id     INT,
                created_at    DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                message     VARCHAR(255) NOT NULL,
                link        VARCHAR(255) DEFAULT '#',
                is_read     TINYINT(1) DEFAULT 0,
                created_at  DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Performance indexes for frequent queries, joins, and filtering
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment (status)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment (category)",
            "CREATE INDEX IF NOT EXISTS idx_equipment_is_deleted ON equipment (is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_mr_status ON maintenance_requests (status)",
            "CREATE INDEX IF NOT EXISTS idx_mr_date_reported ON maintenance_requests (date_reported)",
            "CREATE INDEX IF NOT EXISTS idx_mr_reported_by ON maintenance_requests (reported_by)",
            "CREATE INDEX IF NOT EXISTS idx_mr_equipment_id ON maintenance_requests (equipment_id)",
            "CREATE INDEX IF NOT EXISTS idx_ml_equipment_id ON maintenance_logs (equipment_id)",
            "CREATE INDEX IF NOT EXISTS idx_ml_request_id ON maintenance_logs (request_id)",
            "CREATE INDEX IF NOT EXISTS idx_ml_date_completed ON maintenance_logs (date_completed)",
            "CREATE INDEX IF NOT EXISTS idx_act_created_at ON activity_logs (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notif_user_read ON notifications (user_id, is_read)",
        ]
        for idx_sql in indexes:
            try:
                cur.execute(idx_sql)
            except Exception:
                pass

        # Ensure default system accounts exist if users table is empty
        try:
            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] == 0:
                import bcrypt
                default_users = [
                    ("Administrator", "admin@school.edu", "admin", "admin123"),
                    ("Custodian", "custodian@school.edu", "custodian", "custodian123"),
                    ("Technician", "technician@school.edu", "technician", "technician123"),
                    ("Faculty", "faculty@school.edu", "faculty", "faculty123"),
                ]
                now_str = datetime.now(timezone.utc).replace(tzinfo=None)
                for uname, uemail, urole, upass in default_users:
                    hpass = bcrypt.hashpw(upass.encode(), bcrypt.gensalt()).decode()
                    cur.execute(
                        "INSERT INTO users (name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s)",
                        (uname, uemail, hpass, urole, now_str),
                    )
        except Exception:
            pass

        cnx.commit()
        cur.close()
        _initialized = True

    return cnx


def oid(val):
    try:
        return int(str(val).strip()) if val not in (None, "") else None
    except Exception:
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_notification(db, user_id, message, link="#"):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO notifications (user_id, message, link, is_read, created_at) VALUES (%s, %s, %s, 0, %s)",
        (user_id, message, link or "#", now_utc().replace(tzinfo=None)),
    )
    db.commit()
    cur.close()


def log_activity(db, actor_id, action, details=None, target_type=None, target_id=None):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO activity_logs (actor_id, action, details, target_type, target_id, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (actor_id, action, details or "", target_type, target_id, now_utc().replace(tzinfo=None)),
    )
    db.commit()
    cur.close()


def backup_database(output_path):
    db_name = config.MYSQL_DB
    cmd = [
        "mysqldump",
        "--host", config.MYSQL_HOST,
        "--port", str(config.MYSQL_PORT),
        "--user", config.MYSQL_USER,
    ]
    if config.MYSQL_PASSWORD:
        cmd.append(f"--password={config.MYSQL_PASSWORD}")
    cmd.append(db_name)

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        subprocess.run(cmd, check=True, stdout=handle)
    return output_path


def peso(amount) -> str:
    try:
        return f"₱{float(amount):,.2f}"
    except Exception:
        return "₱0.00"


def status_badge(status: str) -> str:
    mapping = {
        "Working": "badge-success",
        "Resolved": "badge-success",
        "Under Repair": "badge-warning",
        "Under Maintenance": "badge-warning",
        "In Progress": "badge-warning",
        "Pending": "badge-warning",
        "Not Working": "badge-danger",
        "Damaged": "badge-danger",
        "Rejected": "badge-danger",
    }
    return mapping.get(status, "badge-info")


def format_duration_minutes(minutes) -> str:
    if minutes is None:
        return "—"
    try:
        total_mins = int(round(float(minutes)))
    except Exception:
        return "—"
    if total_mins < 0:
        return "—"
    hours = total_mins // 60
    mins = total_mins % 60
    if hours > 0:
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    elif mins > 0:
        return f"{mins}m"
    else:
        return "< 1m"


def format_date(val) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)
