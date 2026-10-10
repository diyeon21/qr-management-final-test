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
    conn_kwargs = {
        "host": config.MYSQL_HOST,
        "port": config.MYSQL_PORT,
        "user": config.MYSQL_USER,
        "password": config.MYSQL_PASSWORD,
        "database": config.MYSQL_DB,
        "ssl_disabled": getattr(config, "MYSQL_SSL_DISABLED", True),
        "autocommit": False,
    }
    if getattr(config, "MYSQL_SSL_CA", ""):
        conn_kwargs["ssl_ca"] = config.MYSQL_SSL_CA

    if _pool is None:
        try:
            boot_kwargs = dict(conn_kwargs)
            boot_kwargs.pop("database", None)
            bootstrap = mysql.connector.connect(**boot_kwargs)
            bcur = bootstrap.cursor()
            bcur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB}`")
            bootstrap.commit()
            bcur.close()
            bootstrap.close()
        except Exception:
            pass

        pool_size = max(5, min(32, getattr(config, "MYSQL_POOL_SIZE", 16)))
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="webbased_pool",
                pool_size=pool_size,
                **conn_kwargs,
            )
        except Exception:
            _pool = None

    cnx = None
    if _pool is not None:
        try:
            cnx = _pool.get_connection()
        except Exception:
            cnx = None

    if cnx is None:
        cnx = mysql.connector.connect(**conn_kwargs)

    try:
        cnx.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        pass

    if not _initialized:
        cur = cnx.cursor(buffered=True)
        
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

        columns_to_ensure = [
            ("users", "is_deleted", "TINYINT(1) NOT NULL DEFAULT 0"),
            ("users", "deleted_at", "DATETIME NULL"),
            ("equipment", "is_deleted", "TINYINT(1) NOT NULL DEFAULT 0"),
            ("equipment", "deleted_at", "DATETIME NULL"),
            ("maintenance_requests", "is_deleted", "TINYINT(1) NOT NULL DEFAULT 0"),
            ("maintenance_requests", "deleted_at", "DATETIME NULL"),
            ("maintenance_requests", "technician_id", "INT NULL"),
            ("maintenance_requests", "affected_component", "VARCHAR(100) NULL"),
            ("maintenance_requests", "repair_start", "DATETIME NULL"),
            ("maintenance_requests", "technician_notes", "TEXT NULL"),
            ("maintenance_logs", "repair_start", "DATETIME NULL"),
            ("maintenance_logs", "duration_minutes", "INT NULL"),
            ("maintenance_logs", "technician_id", "INT NULL"),
        ]

        for tbl, col, col_def in columns_to_ensure:
            try:
                cur.execute(f"SHOW COLUMNS FROM `{tbl}` LIKE %s", (col,))
                existing_cols = cur.fetchall()
                if not existing_cols:
                    cur.execute(f"ALTER TABLE `{tbl}` ADD COLUMN `{col}` {col_def}")
                    cnx.commit()
            except Exception:
                try:
                    cur.execute(f"ALTER TABLE `{tbl}` ADD COLUMN IF NOT EXISTS `{col}` {col_def}")
                    cnx.commit()
                except Exception:
                    pass

        try:
            cur.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin','custodian','technician','faculty') NOT NULL DEFAULT 'faculty'")
            cnx.commit()
        except Exception:
            pass

        try:
            cur.execute("ALTER TABLE maintenance_requests ADD CONSTRAINT fk_technician FOREIGN KEY (technician_id) REFERENCES users(id) ON DELETE SET NULL")
            cnx.commit()
        except Exception:
            pass

        # Performance indexes for frequent queries, joins, and filtering
        indexes_to_ensure = [
            ("users", "idx_users_role", "role"),
            ("equipment", "idx_equipment_status", "status"),
            ("equipment", "idx_equipment_category", "category"),
            ("equipment", "idx_equipment_is_deleted", "is_deleted"),
            ("maintenance_requests", "idx_mr_status", "status"),
            ("maintenance_requests", "idx_mr_date_reported", "date_reported"),
            ("maintenance_requests", "idx_mr_reported_by", "reported_by"),
            ("maintenance_requests", "idx_mr_equipment_id", "equipment_id"),
            ("maintenance_logs", "idx_ml_equipment_id", "equipment_id"),
            ("maintenance_logs", "idx_ml_request_id", "request_id"),
            ("maintenance_logs", "idx_ml_date_completed", "date_completed"),
            ("activity_logs", "idx_act_created_at", "created_at"),
            ("notifications", "idx_notif_user_read", "user_id, is_read"),
        ]
        for tbl, idx_name, idx_cols in indexes_to_ensure:
            try:
                cur.execute(f"SHOW INDEX FROM `{tbl}` WHERE Key_name = %s", (idx_name,))
                existing_idxs = cur.fetchall()
                if not existing_idxs:
                    cur.execute(f"CREATE INDEX `{idx_name}` ON `{tbl}` ({idx_cols})")
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
