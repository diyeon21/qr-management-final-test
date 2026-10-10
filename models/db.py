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
        conn_kwargs = {
            "host": config.MYSQL_HOST,
            "port": config.MYSQL_PORT,
            "user": config.MYSQL_USER,
            "password": config.MYSQL_PASSWORD,
            "ssl_disabled": getattr(config, "MYSQL_SSL_DISABLED", True),
        }
        if getattr(config, "MYSQL_SSL_CA", ""):
            conn_kwargs["ssl_ca"] = config.MYSQL_SSL_CA


        try:
            bootstrap = mysql.connector.connect(**conn_kwargs)
            bcur = bootstrap.cursor()
            bcur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB}`")
            bootstrap.commit()
            bcur.close()
            bootstrap.close()
        except Exception:
            # In managed cloud databases (e.g. TiDB, RDS, Clever Cloud), user may not have CREATE DATABASE permissions
            pass

        pool_size = max(1, min(32, getattr(config, "MYSQL_POOL_SIZE", 8)))
        _pool = pooling.MySQLConnectionPool(
            pool_name="webbased_pool",
            pool_size=pool_size,
            database=config.MYSQL_DB,
            autocommit=False,
            **conn_kwargs,
        )


    cnx = _pool.get_connection()
    try:
        cnx.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        pass

    if not _initialized:
        cur = cnx.cursor()
        
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                email       VARCHAR(255) NOT NULL UNIQUE,
                password    VARCHAR(255) NOT NULL,
                role        ENUM('admin','custodian','technician','faculty') NOT NULL DEFAULT 'faculty',
                created_at  DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                name              VARCHAR(255) NOT NULL,
                category          VARCHAR(255),
                location          VARCHAR(255),
                status            VARCHAR(64) DEFAULT 'Working',
                qr_code           TEXT,
                created_at        DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
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
                is_deleted          TINYINT(1) NOT NULL DEFAULT 0,
                deleted_at          DATETIME NULL,
                technician_id       INT NULL,
                repair_start        DATETIME NULL,
                technician_notes    TEXT NULL,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (reported_by)  REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                equipment_id    INT NOT NULL,
                request_id      INT NOT NULL,
                action_taken    TEXT,
                date_completed  DATETIME NOT NULL,
                repair_start    DATETIME NULL,
                duration_minutes INT NULL,
                technician_id   INT NULL,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (request_id)   REFERENCES maintenance_requests(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                actor_id      INT,
                action        VARCHAR(255) NOT NULL,
                details       TEXT,
                target_type   VARCHAR(100),
                target_id     INT,
                created_at    DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                message     VARCHAR(255) NOT NULL,
                link        VARCHAR(255) DEFAULT '#',
                is_read     TINYINT(1) DEFAULT 0,
                created_at  DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        ]

        for tbl_sql in tables:
            try:
                cur.execute(tbl_sql)
                cnx.commit()
            except Exception:
                pass

        migrations = [
            "ALTER TABLE users MODIFY COLUMN role ENUM('admin','custodian','technician','faculty') NOT NULL DEFAULT 'faculty'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL",
            "ALTER TABLE equipment ADD COLUMN IF NOT EXISTS is_deleted TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE equipment ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS is_deleted TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS technician_id INT NULL",
            "ALTER TABLE maintenance_requests ADD CONSTRAINT fk_technician FOREIGN KEY (technician_id) REFERENCES users(id) ON DELETE SET NULL",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS affected_component VARCHAR(100) NULL",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS repair_start DATETIME NULL",
            "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS technician_notes TEXT NULL",
            "ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS repair_start DATETIME NULL",
            "ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS duration_minutes INT NULL",
            "ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS technician_id INT NULL",
        ]

        for mig in migrations:
            try:
                cur.execute(mig)
                cnx.commit()
            except Exception:
                if "ADD COLUMN IF NOT EXISTS" in mig:
                    try:
                        fallback = mig.replace("ADD COLUMN IF NOT EXISTS", "ADD COLUMN")
                        cur.execute(fallback)
                        cnx.commit()
                    except Exception:
                        pass

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
                cnx.commit()
            except Exception:
                if "CREATE INDEX IF NOT EXISTS" in idx_sql:
                    try:
                        fallback_idx = idx_sql.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX")
                        cur.execute(fallback_idx)
                        cnx.commit()
                    except Exception:
                        pass

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
        "Completed - Pending Verification": "badge-info",
        "Pending Verification": "badge-info",
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
