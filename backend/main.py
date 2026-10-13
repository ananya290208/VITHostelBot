import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from complaint_manager import load_complaints, create_complaint, get_complaint
from bot_service import process_with_gemini, RULES_DATA, MESS_DATA, UTILITIES_DATA

app = FastAPI(
    title="Campus Hostel Information & Complaint Management AI",
    version="1.0.0",
    description="Intelligent Assistant for Hostel Rules, Mess Menus, Complaints (AC/Wi-Fi/Water Cooler), and Utilities"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    reply: str
    ticket: Optional[Dict[str, Any]] = None
    engine: str

class ComplaintRequest(BaseModel):
    category: str
    room_number: str
    description: str
    urgency: Optional[str] = "Normal"

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = process_with_gemini(payload.message, payload.chat_history)
    return result

@app.get("/api/complaints")
def list_all_complaints():
    return load_complaints()

@app.post("/api/complaints")
def submit_complaint(complaint: ComplaintRequest):
    new_ticket = create_complaint(
        category=complaint.category,
        room_number=complaint.room_number,
        description=complaint.description,
        urgency=complaint.urgency
    )
    return new_ticket

@app.get("/api/complaints/{ticket_id}")
def check_status(ticket_id: str):
    ticket = get_complaint(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Complaint ticket not found")
    return ticket

@app.get("/api/knowledge/{category}")
def get_knowledge(category: str):
    cat = category.lower()
    if cat == "rules":
        return RULES_DATA
    elif cat == "mess":
        return MESS_DATA
    elif cat == "utilities":
        return UTILITIES_DATA
    else:
        raise HTTPException(status_code=404, detail="Category not found. Use 'rules', 'mess', or 'utilities'.")

# Mount frontend static directory if exists
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
