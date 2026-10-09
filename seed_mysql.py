import bcrypt
from models import get_db, now_utc

DEFAULT_USERS = [
    ("Administrator", "admin@school.edu", "admin", "admin123"),
    ("Custodian", "custodian@school.edu", "custodian", "custodian123"),
    ("Technician", "technician@school.edu", "technician", "technician123"),
    ("Faculty", "faculty@school.edu", "faculty", "faculty123"),
]

def main():
    db = get_db()
    cur = db.cursor(dictionary=True)
    created = 0

    for name, email, role, password in DEFAULT_USERS:
        cur.execute("SELECT id FROM users WHERE email=%s LIMIT 1", (email,))
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE users SET name=%s, role=%s WHERE id=%s", (name, role, existing["id"]))
            continue
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s)",
            (name, email, hashed, role, now_utc().replace(tzinfo=None)),
        )
        created += 1

    db.commit()
    cur.close()
    db.close()
    print(f"Seed complete. Processed users.")

if __name__ == "__main__":
    main()
