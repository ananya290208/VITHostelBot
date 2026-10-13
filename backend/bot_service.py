import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List

from complaint_manager import create_complaint, get_complaint, load_complaints

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def read_json_data(filename: str) -> Dict:
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

RULES_DATA = read_json_data("rules.json")
MESS_DATA = read_json_data("mess_menu.json")
UTILITIES_DATA = read_json_data("utilities.json")

def get_current_day_name() -> str:
    return datetime.now().strftime("%A").lower()

def format_knowledge_context() -> str:
    return f"""
YOU ARE THE CAMPUS HOSTEL INFORMATION MANAGEMENT AI ASSISTANT.
Current Time / Date: {datetime.now().strftime("%A, %d %B %Y, %I:%M %p")}

HOSTEL RULES & TIMINGS KNOWLEDGE:
{json.dumps(RULES_DATA, indent=2)}

MESS & DINING SCHEDULE & WEEKLY MENU:
{json.dumps(MESS_DATA, indent=2)}

UTILITIES (HOT WATER, IRON BOX, LAUNDRY, WATER COOLERS):
{json.dumps(UTILITIES_DATA, indent=2)}

YOUR RESPONSIBILITIES:
1. Provide accurate answers regarding hostel rules, curfew timings, library pass extension, and night out pass check-in/out procedures.
2. Provide mess timings and daily/weekly meal menu based on day of the week.
3. Provide hot water geyser timings and iron box location & usage rules.
4. For complaints regarding AC, Water Cooler, Wi-Fi, Electrical, Plumbing, or Carpentry:
   - Ask for or identify the Room Number/Location and issue details.
   - Use the `register_complaint` function to log a ticket and return the Ticket ID clearly.
5. If the student asks about an existing ticket status, use `check_complaint_status`.
6. Be courteous, clear, and concise. Format lists with markdown bullet points.
"""

# Gemini SDK integration with fallback
def process_with_gemini(message: str, chat_history: List[Dict]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback heuristic engine if no API key is provided
        return rule_based_fallback(message)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        def tool_register_complaint(category: str, room_number: str, description: str, urgency: str = "Normal") -> dict:
            return create_complaint(category, room_number, description, urgency)

        def tool_check_complaint_status(ticket_id: str) -> dict:
            ticket = get_complaint(ticket_id)
            if ticket:
                return ticket
            return {"error": f"Ticket {ticket_id} not found. Please verify the ID."}

        def tool_get_mess_menu(day: str = "today") -> dict:
            target_day = get_current_day_name() if day.lower() in ["today", "now"] else day.lower()
            menu = MESS_DATA.get("weekly_menu", {}).get(target_day)
            return {
                "day": target_day.capitalize(),
                "timings": MESS_DATA.get("mess_timings", {}),
                "menu": menu or "Menu not found for given day."
            }

        tools = [tool_register_complaint, tool_check_complaint_status, tool_get_mess_menu]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=format_knowledge_context(),
                tools=tools,
                temperature=0.2
            )
        )

        ticket_card = None
        # Check if function call was made
        if response.function_calls:
            for call in response.function_calls:
                if call.name == "tool_register_complaint":
                    args = call.args
                    ticket_card = create_complaint(
                        args.get("category", "General"),
                        args.get("room_number", "Unspecified"),
                        args.get("description", message),
                        args.get("urgency", "Normal")
                    )

        reply_text = response.text or "I have processed your request."
        return {
            "reply": reply_text,
            "ticket": ticket_card,
            "engine": "gemini"
        }

    except Exception as e:
        print(f"Gemini API call failed or timed out: {e}. Falling back to local engine.")
        return rule_based_fallback(message)


def rule_based_fallback(query: str) -> Dict[str, Any]:
    """Smart offline assistant for seamless local testing without API key"""
    q = query.lower()
    today = get_current_day_name()
    ticket_created = None

    # 1. Complaints Intent (AC, Wi-Fi, Water cooler, etc.)
    if any(k in q for k in ["complaint", "not working", "broken", "issue", "leaking", "repair", "ticket"]):
        # Check for status lookup
        ticket_match = re.search(r"tkt-\d{4}-\d{3}", q, re.IGNORECASE)
        if ticket_match or "status" in q:
            if ticket_match:
                t_id = ticket_match.group(0).upper()
                ticket = get_complaint(t_id)
                if ticket:
                    return {
                        "reply": f"📋 **Ticket Status for {ticket['ticket_id']}**:\n- **Category:** {ticket['category']}\n- **Room/Location:** {ticket['room_number']}\n- **Status:** **{ticket['status']}**\n- **Assigned To:** {ticket['assigned_to']}\n- **Notes:** {ticket['resolution_notes']}",
                        "ticket": ticket,
                        "engine": "local"
                    }
                else:
                    return {
                        "reply": f"❌ Could not find any ticket with ID **{t_id}**. Please check the ticket number.",
                        "engine": "local"
                    }
            else:
                return {
                    "reply": "Please provide your Ticket ID (e.g. `TKT-2026-001`) to check the status.",
                    "engine": "local"
                }

        # New Complaint creation
        category = "General"
        if "ac" in q or "air condition" in q:
            category = "AC"
        elif "wifi" in q or "wi-fi" in q or "internet" in q or "network" in q:
            category = "Wi-Fi"
        elif "water cooler" in q or "cooler" in q or "ro" in q or "drinking water" in q:
            category = "Water Cooler"
        elif "plumbing" in q or "tap" in q or "geyser" in q or "flush" in q:
            category = "Plumbing"
        elif "light" in q or "fan" in q or "switch" in q or "power" in q:
            category = "Electrical"

        # Try to extract room number
        room_match = re.search(r"\b([a-bA-B][ -]?\d{3}|\d{3})\b", query)
        room_no = room_match.group(0).upper() if room_match else "Hostel Resident Room"

        ticket_created = create_complaint(
            category=category,
            room_number=room_no,
            description=query,
            urgency="High" if "urgent" in q or "emergency" in q else "Normal"
        )
        return {
            "reply": f"✅ **Complaint Registered Successfully!**\n\n- **Ticket ID:** `{ticket_created['ticket_id']}`\n- **Category:** {ticket_created['category']}\n- **Location/Room:** {ticket_created['room_number']}\n- **Assigned Caretaker:** {ticket_created['assigned_to']}\n- **Status:** {ticket_created['status']}\n\nA technician will inspect the issue within 24 hours. You can ask me anytime: *'What is the status of {ticket_created['ticket_id']}?'*",
            "ticket": ticket_created,
            "engine": "local"
        }

    # 2. Hot Water / Geyser Timings
    if any(k in q for k in ["hot water", "geyser", "warm water", "bath"]):
        hw = UTILITIES_DATA.get("hot_water_facility", {})
        timings = hw.get("timings", {})
        return {
            "reply": f"🚿 **Hot Water (Geyser) Availability:**\n\n- 🌅 **Morning:** {timings.get('morning', '06:00 AM - 09:30 AM')}\n- 🌆 **Evening:** {timings.get('evening', '06:30 PM - 09:00 PM')}\n\n💡 *Note:* {hw.get('seasonal_notes', '')} Hot water is supplied to all attached and common washrooms.",
            "engine": "local"
        }

    # 3. Iron Box / Laundry Facilities
    if any(k in q for k in ["iron", "iron box", "press", "ironing"]):
        iron = UTILITIES_DATA.get("iron_box_facility", {})
        locations = "\n".join([f"  • {loc}" for loc in iron.get("locations", [])])
        return {
            "reply": f"👔 **Iron Box Availability & Locations:**\n\n{locations}\n\n- **Hours:** {iron.get('operating_hours', '07:00 AM - 10:00 PM daily')}\n- **Rules:** Heavy-duty steam irons and boards are available in common rooms. For fire safety, *personal high-wattage irons in bedrooms are prohibited*.",
            "engine": "local"
        }

    # 4. Mess & Food Information
    if any(k in q for k in ["mess", "food", "breakfast", "lunch", "dinner", "snack", "menu"]):
        timings = MESS_DATA.get("mess_timings", {})
        weekly = MESS_DATA.get("weekly_menu", {})

        # Check if asking for a specific day
        selected_day = today
        for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if day_name in q:
                selected_day = day_name
                break

        day_menu = weekly.get(selected_day, {})

        if "breakfast" in q:
            meal_desc = f"🍳 **{selected_day.capitalize()} Breakfast ({timings.get('breakfast')}):**\n{day_menu.get('breakfast')}"
        elif "lunch" in q:
            meal_desc = f"🍛 **{selected_day.capitalize()} Lunch ({timings.get('lunch')}):**\n{day_menu.get('lunch')}"
        elif "snack" in q:
            meal_desc = f"☕ **{selected_day.capitalize()} High Tea / Snacks ({timings.get('snacks')}):**\n{day_menu.get('snacks')}"
        elif "dinner" in q:
            meal_desc = f"🍲 **{selected_day.capitalize()} Dinner ({timings.get('dinner')}):**\n{day_menu.get('dinner')}"
        else:
            meal_desc = f"""🍽️ **Today's Mess Menu ({selected_day.capitalize()}):**
- 🍳 **Breakfast ({timings.get('breakfast')}):** {day_menu.get('breakfast')}
- 🍛 **Lunch ({timings.get('lunch')}):** {day_menu.get('lunch')}
- ☕ **Snacks ({timings.get('snacks')}):** {day_menu.get('snacks')}
- 🍲 **Dinner ({timings.get('dinner')}):** {day_menu.get('dinner')}"""

        return {
            "reply": meal_desc,
            "engine": "local"
        }

    # 5. Rules, Curfew, Gate Timings & Check-in/out
    if any(k in q for k in ["curfew", "timing", "gate", "late", "check in", "check out", "night out", "pass", "leave", "rule"]):
        curfew = RULES_DATA.get("curfew_and_timings", {})
        checkout = RULES_DATA.get("check_in_and_check_out", {})
        rules_list = "\n".join([f"• {r}" for r in curfew.get("curfew_rules", [])])

        return {
            "reply": f"🚪 **Hostel Timings & Curfew Guidelines:**\n\n- **Main Gate Closes:** {curfew.get('main_gate_closing', '10:00 PM')} (Strict)\n- **Main Gate Opens:** {curfew.get('main_gate_opening', '06:00 AM')}\n- **Library Study Extension:** {curfew.get('library_pass_extension', {}).get('allowed_time', 'Till 11:30 PM')} (Requires library pass slip)\n\n📌 **Key Rules:**\n{rules_list}\n\n📝 **Night Out Pass:** Must apply before 06:00 PM with registered parent confirmation.",
            "engine": "local"
        }

    # General greeting / fallback
    return {
        "reply": "👋 Hello! I am your **Campus Hostel AI Assistant**.\n\nI can help you with:\n1. 🚪 **Hostel Rules & Curfew** (Gate timings, check-in/out, library passes)\n2. 🛠️ **Maintenance Complaints** (Report AC, Wi-Fi, Water cooler, or plumbing issues)\n3. 🍽️ **Mess Menu & Timings** (Daily breakfast, lunch, snacks, dinner options)\n4. 🚿 **Facilities & Utilities** (Hot water geyser hours, iron box availability)\n\nHow can I help you today?",
        "engine": "local"
    }
