import random
from models import get_db

def get_description(name, category):
    if "Printer" in name:
        return random.choice(["Paper jam in tray 2.", "Out of toner.", "Network connection lost."])
    if "Air Conditioner" in name:
        return random.choice(["Filter needs cleaning.", "Not cooling properly.", "Making loud noises.", "Water leaking."])
    if "Projector" in name:
        return random.choice(["Bulb needs replacement.", "Device will not turn on.", "Image is blurry."])
    if "Whiteboard" in name:
        return random.choice(["Surface won't erase cleanly.", "Frame is loose.", "Marker tray broken.", "Mounting bracket damaged."])
    if "Desk" in name or "Chair" in name:
        return random.choice(["Leg is broken.", "Wobbly.", "Surface is scratched.", "Backrest is loose."])
    if "Laptop" in name or "PC" in name:
        return random.choice(["Screen is flickering.", "Overheating after 10 minutes of use.", "Keys are stuck.", "Device will not turn on."])
    if "Network Switch" in name or "Router" in name:
        return random.choice(["Network drops frequently.", "Device will not turn on.", "Port 4 is dead."])
    if "Speaker" in name or "Microphone" in name:
        return random.choice(["No audio output.", "Making static noises.", "Cable frayed."])
    
    return random.choice(["Device will not turn on.", "Missing power cable.", "Physical damage."])

def get_action(name, category):
    if "Printer" in name:
        return random.choice(["Cleared paper jam.", "Replaced toner cartridge.", "Reset network config."])
    if "Air Conditioner" in name:
        return random.choice(["Cleaned filter and condenser.", "Recharged freon.", "Tightened loose fan belt.", "Unclogged drain pipe."])
    if "Projector" in name:
        return random.choice(["Replaced projection bulb.", "Replaced power supply.", "Cleaned lens."])
    if "Whiteboard" in name:
        return random.choice(["Deep cleaned surface.", "Tightened mounting screws.", "Replaced marker tray."])
    if "Desk" in name or "Chair" in name:
        return random.choice(["Glued and screwed broken leg.", "Tightened all bolts.", "Polished surface."])
    if "Laptop" in name or "PC" in name:
        return random.choice(["Replaced display cable.", "Cleaned internal fans and applied thermal paste.", "Replaced keyboard module.", "Replaced battery."])
    if "Network Switch" in name or "Router" in name:
        return random.choice(["Updated firmware.", "Replaced power adapter.", "Reset to factory defaults."])
    if "Speaker" in name or "Microphone" in name:
        return random.choice(["Replaced audio cable.", "Soldered loose connection.", "Replaced amplifier module."])

    return random.choice(["Replaced faulty parts and tested.", "Cleaned internals.", "Tightened loose connections."])


def fix_data():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT mr.id as req_id, e.name, e.category FROM maintenance_requests mr JOIN equipment e ON e.id = mr.equipment_id")
    requests = cur.fetchall()
    
    for r in requests:
        new_desc = get_description(r['name'], r['category'])
        cur.execute("UPDATE maintenance_requests SET description=%s WHERE id=%s", (new_desc, r['req_id']))
        
        # Check if there is an associated log
        cur.execute("SELECT id FROM maintenance_logs WHERE request_id=%s", (r['req_id'],))
        log = cur.fetchone()
        if log:
            new_action = get_action(r['name'], r['category'])
            cur.execute("UPDATE maintenance_logs SET action_taken=%s WHERE id=%s", (new_action, log['id']))
            
    db.commit()
    cur.close()
    db.close()
    print("Data fixed successfully!")

if __name__ == '__main__':
    fix_data()
