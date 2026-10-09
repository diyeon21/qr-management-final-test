import mysql.connector
import random
from datetime import datetime, timedelta
import urllib.parse
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def run_seed():
    db = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cur = db.cursor(dictionary=True)

    print("Cleaning existing records...")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("TRUNCATE TABLE maintenance_logs")
    cur.execute("TRUNCATE TABLE maintenance_requests")
    cur.execute("TRUNCATE TABLE equipment")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Fetch users
    cur.execute("SELECT id, role FROM users")
    users = cur.fetchall()
    faculties = [u['id'] for u in users if u['role'] == 'faculty']
    custodians = [u['id'] for u in users if u['role'] == 'custodian']
    
    if not faculties: faculties = [None]
    if not custodians: custodians = [None]

    equipment_templates = [
        {"name": "Whiteboard", "category": "Classroom"},
        {"name": "Student Chair", "category": "Furniture"},
        {"name": "Teachers Desk", "category": "Furniture"},
        {"name": "Epson Projector", "category": "AV Equipment"},
        {"name": "Air Conditioner", "category": "Facilities"},
        {"name": "Lenovo Desktop PC", "category": "IT Equipment"},
        {"name": "HP LaserJet Printer", "category": "IT Equipment"},
        {"name": "Network Switch", "category": "IT Equipment"},
        {"name": "PA Speaker", "category": "AV Equipment"},
        {"name": "Microphone", "category": "AV Equipment"}
    ]

    print("Generating 50 simple equipment records...")
    equipment_ids = []
    
    # 3 floors, RM 101-110, 201-210, 301-310
    labs = [f"Laboratory {i}" for i in range(1, 8)]

    for i in range(1, 51):
        tmpl = random.choice(equipment_templates)
        name = f"{tmpl['name']} - {i:02d}"
        category = tmpl['category']
        location = random.choice(labs)
        
        # 80% Working, 12% Under Repair, 8% Not Working
        rnd = random.random()
        if rnd < 0.80:
            status = "Working"
        elif rnd < 0.92:
            status = "Under Repair"
        else:
            status = "Not Working"
        
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(name)}"

        cur.execute(
            "INSERT INTO equipment (name, category, location, purchase_cost, status, qr_code) VALUES (%s, %s, %s, 0, %s, %s)",
            (name, category, location, status, qr_url)
        )
        equipment_ids.append(cur.lastrowid)

    db.commit()

    print("Generating sensible maintenance requests...")
    
    def get_issue(name):
        if "Printer" in name: return random.choice(["Paper jam in tray 2.", "Out of toner.", "Network connection lost."])
        if "Air Conditioner" in name: return random.choice(["Filter needs cleaning.", "Not cooling properly.", "Water leaking from vent."])
        if "Projector" in name: return random.choice(["Bulb needs replacement.", "Image is very blurry.", "Won't turn on."])
        if "Whiteboard" in name: return random.choice(["Surface won't erase cleanly.", "Marker tray broken.", "Mounting bracket loose."])
        if "Desk" in name or "Chair" in name: return random.choice(["Leg is broken.", "Wobbly.", "Surface is heavily scratched."])
        if "PC" in name: return random.choice(["Screen is flickering.", "Blue screen of death.", "Keyboard keys stuck."])
        if "Network" in name: return random.choice(["Network drops frequently.", "Port 4 is dead."])
        if "Speaker" in name or "Microphone" in name: return random.choice(["No audio output.", "Cable is frayed.", "Making static noises."])
        return "Device is malfunctioning."

    def get_action(name):
        if "Printer" in name: return random.choice(["Cleared paper jam.", "Replaced toner cartridge."])
        if "Air Conditioner" in name: return random.choice(["Cleaned filter and condenser.", "Recharged freon.", "Unclogged drain pipe."])
        if "Projector" in name: return random.choice(["Replaced projection bulb.", "Cleaned lens."])
        if "Whiteboard" in name: return random.choice(["Deep cleaned surface with solvent.", "Replaced marker tray."])
        if "Desk" in name or "Chair" in name: return random.choice(["Glued and screwed broken leg.", "Tightened all bolts."])
        if "PC" in name: return random.choice(["Replaced display cable.", "Replaced keyboard module."])
        if "Network" in name: return random.choice(["Updated firmware.", "Replaced power adapter."])
        if "Speaker" in name or "Microphone" in name: return random.choice(["Replaced audio cable.", "Soldered loose connection."])
        return "Tested and replaced faulty components."

    now = datetime.now()
    
    # Let's create about 20 requests
    cur.execute("SELECT id, name FROM equipment")
    eq_list = cur.fetchall()

    for _ in range(20):
        eq = random.choice(eq_list)
        reporter = random.choice(faculties)
        desc = get_issue(eq['name'])
        urgency = random.choice(["Low", "Medium", "High", "Critical"])
        
        # Determine status
        if eq['id'] % 5 == 0:
            status = "Pending"
        elif eq['id'] % 7 == 0:
            status = "In Progress"
        else:
            status = "Resolved"
            
        date_reported = now - timedelta(days=random.randint(1, 30), hours=random.randint(1, 24))
        
        cur.execute(
            "INSERT INTO maintenance_requests (equipment_id, reported_by, description, urgency, status, date_reported) VALUES (%s, %s, %s, %s, %s, %s)",
            (eq['id'], reporter, desc, urgency, status, date_reported)
        )
        req_id = cur.lastrowid
        
        if status == "Resolved":
            date_responded = date_reported + timedelta(hours=random.randint(1, 5))
            date_completed = date_responded + timedelta(hours=random.randint(1, 48))
            action = get_action(eq['name'])
            
            cur.execute("UPDATE maintenance_requests SET date_responded=%s WHERE id=%s", (date_responded, req_id))
            cur.execute(
                "INSERT INTO maintenance_logs (equipment_id, request_id, cost, action_taken, date_completed) VALUES (%s, %s, 0, %s, %s)",
                (eq['id'], req_id, action, date_completed)
            )

    db.commit()
    cur.close()
    db.close()
    print("Database freshly seeded with 50 items and sensible requests for presentation!")

if __name__ == '__main__':
    run_seed()
