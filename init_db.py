import sys
from models import get_db
import seed_mysql

def reset_data():
    db = get_db()
    cur = db.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ["maintenance_logs", "maintenance_requests", "activity_logs", "notifications", "equipment", "users"]:
        cur.execute(f"TRUNCATE TABLE `{table}`")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()
    cur.close()
    db.close()
    seed_mysql.main()


def initialize(seed: bool = False, reset: bool = False):
    if reset:
        reset_data()
        return

    cnx = get_db()
    cnx.close()

    if seed:
        seed_mysql.main()


if __name__ == "__main__":
    should_reset = "--reset" in sys.argv or "--clean-data" in sys.argv
    should_seed = "--seed" in sys.argv or should_reset
    try:
        initialize(seed=should_seed, reset=should_reset)
    except Exception as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
