import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
COMPLAINTS_FILE = os.path.join(DATA_DIR, "complaints.json")

def load_complaints() -> List[Dict]:
    if not os.path.exists(COMPLAINTS_FILE):
        return []
    try:
        with open(COMPLAINTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_complaints(complaints: List[Dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(COMPLAINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(complaints, f, indent=2)

def create_complaint(category: str, room_number: str, description: str, urgency: str = "Normal") -> Dict:
    complaints = load_complaints()
    ticket_num = len(complaints) + 1
    ticket_id = f"TKT-{datetime.now().year}-{ticket_num:03d}"
    
    # Assign automated technician based on category
    assigned_map = {
        "AC": "Mr. Suresh (HVAC Tech)",
        "Wi-Fi": "Campus IT Support (Ext: 4402)",
        "Water Cooler": "Mr. Ramesh (Plumbing & RO Caretaker)",
        "Electrical": "Mr. Vinod (Campus Electrician)",
        "Plumbing": "Mr. Ramesh (Plumbing & RO Caretaker)",
        "General": "Hostel Caretaker Office"
    }
    
    assigned_to = assigned_map.get(category, "Hostel Caretaker Office")
    
    new_ticket = {
        "ticket_id": ticket_id,
        "category": category,
        "room_number": room_number,
        "description": description,
        "urgency": urgency,
        "status": "Pending",
        "created_at": datetime.now().isoformat(),
        "assigned_to": assigned_to,
        "resolution_notes": "Ticket registered in hostel system. Caretaker notified."
    }
    
    complaints.append(new_ticket)
    save_complaints(complaints)
    return new_ticket

def get_complaint(ticket_id: str) -> Optional[Dict]:
    complaints = load_complaints()
    clean_id = ticket_id.strip().upper()
    for item in complaints:
        if item.get("ticket_id", "").upper() == clean_id:
            return item
    return None
