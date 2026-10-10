"""
Database Initialization & Seeding CLI Utility.
Usage:
    python init_db.py          # Create tables, columns, and indexes
    python init_db.py --seed   # Create schema and seed default user accounts
"""
import sys
from models import get_db
import seed_mysql

def reset_data():
    """Wipes all dummy equipment, requests, logs, and resets to a completely fresh system."""
    db = get_db()
    cur = db.cursor()
    print("[*] Clearing all dummy data and logs...")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ["maintenance_logs", "maintenance_requests", "activity_logs", "notifications", "equipment", "users"]:
        cur.execute(f"TRUNCATE TABLE `{table}`")
        print(f"[-] Cleared table: {table}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()
    cur.close()
    db.close()
    print("[*] Seeding fresh default accounts...")
    seed_mysql.main()
    print("[+] Fresh system initialization complete.")


def initialize(seed: bool = False, reset: bool = False):
    if reset:
        reset_data()
        return

    print("[*] Connecting to database and verifying schema...")
    cnx = get_db()
    print("[+] Database tables and indexes verified successfully.")
    cnx.close()

    if seed:
        print("[*] Seeding default accounts...")
        seed_mysql.main()
        print("[+] Seed operation completed.")


if __name__ == "__main__":
    should_reset = "--reset" in sys.argv or "--clean-data" in sys.argv
    should_seed = "--seed" in sys.argv or should_reset
    try:
        initialize(seed=should_seed, reset=should_reset)
        print("[SUCCESS] Database operations completed.")
    except Exception as e:
        print(f"[ERROR] Database operations failed: {e}", file=sys.stderr)
        sys.exit(1)

