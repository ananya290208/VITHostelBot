# 🏢 Campus Hostel AI ChatBot

An intelligent, modular AI ChatBot for College Hostel Information & Complaint Management.

---

## 🎯 Features Aligned With Requirements

| Requirement | Implementation Details | Data Source |
| :--- | :--- | :--- |
| **1. Hostel Rules & Timings** | Curfew timings (10:00 PM), gate open/close hours, biometric entry rules, library extension (till 11:30 PM), day pass & night out-pass procedures. | [`data/rules.json`](./data/rules.json) |
| **2. Maintenance Complaints** | Natural language complaint registration for **AC, Wi-Fi, Water Coolers, Plumbing, Electrical**. Auto-generates unique Ticket IDs (e.g. `TKT-2026-004`), auto-assigns technicians, and provides live status tracking. | [`data/complaints.json`](./data/complaints.json) |
| **3. Mess Information** | Timings for Breakfast, Lunch, Snacks, Dinner, and 7-day revolving meal menus (Monday to Sunday). | [`data/mess_menu.json`](./data/mess_menu.json) |
| **4. Utilities & Amenities** | Geyser hot water operational hours (Morning & Evening), iron box locations (Common utility rooms), laundry rules, and water dispenser stations. | [`data/utilities.json`](./data/utilities.json) |

---

## 📂 Project Architecture

```
HostelChatBot/
├── data/
│   ├── rules.json             # Curfew, check-in/out, visitor rules
│   ├── mess_menu.json         # Breakfast/Lunch/Dinner timings and 7-day menu
│   ├── utilities.json         # Hot water schedule & iron box locations
│   └── complaints.json        # Persistent ticket store for AC, Wi-Fi, Coolers
├── backend/
│   ├── main.py                # FastAPI web server and API endpoints
│   ├── bot_service.py         # Gemini AI agent + Function Calling + fallback engine
│   ├── complaint_manager.py   # Ticket ID generator & status manager
│   └── requirements.txt       # Dependencies (fastapi, uvicorn, google-genai)
├── frontend/
│   ├── index.html             # Responsive mobile-friendly student UI
│   ├── style.css              # Styling with ticket badges & quick chips
│   └── app.js                 # Chat handling and live ticket sidebar syncing
├── run_hostel_bot.bat         # 1-Click launcher for Windows
└── README.md
```

---

## 🚀 How to Run

### Method 1: Double-click launcher (Windows)
Double-click [`run_hostel_bot.bat`](./run_hostel_bot.bat). It installs requirements if needed and opens `http://localhost:8000`.

### Method 2: Manual Terminal Run
Open PowerShell or Command Prompt in `F:\Ananya\Andriod Club\HostelChatBot`:
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Open your browser at `http://localhost:8000`.

*(Note: If you have a Gemini API key, set `$env:GEMINI_API_KEY="your_key"`. If not set, it runs in **Smart Local Assistant mode** so all rules, timings, hot water queries, and complaints work right away!)*
