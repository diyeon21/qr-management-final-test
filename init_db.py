"""
Database Initialization & Seeding CLI Utility.
Usage:
    python init_db.py          # Create tables, columns, and indexes
    python init_db.py --seed   # Create schema and seed default user accounts
"""
import sys
from models import get_db
import seed_mysql

def initialize(seed: bool = False):
    print("[*] Connecting to database and verifying schema...")
    cnx = get_db()
    print("[+] Database tables and indexes verified successfully.")
    cnx.close()

    if seed:
        print("[*] Seeding default accounts...")
        seed_mysql.main()
        print("[+] Seed operation completed.")

if __name__ == "__main__":
    should_seed = "--seed" in sys.argv
    try:
        initialize(seed=should_seed)
        print("[SUCCESS] Database initialization completed.")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
