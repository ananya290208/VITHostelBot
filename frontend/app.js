const API_BASE = "";
let chatHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  loadRecentTickets();
});

function appendMessage(sender, text, ticketData = null) {
  const container = document.getElementById("messagesArea");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${sender}-message`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "👤" : "🤖";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  // Parse Markdown for bot responses, plain text for user
  if (sender === "bot") {
    contentDiv.innerHTML = marked.parse(text);
  } else {
    contentDiv.textContent = text;
  }

  // If a complaint ticket was created or retrieved, render an interactive ticket card
  if (ticketData) {
    const card = document.createElement("div");
    card.className = "ticket-card";
    const statusClass = getStatusBadgeClass(ticketData.status);
    card.innerHTML = `
      <div class="ticket-card-title">
        <span>🎫 ${ticketData.ticket_id}</span>
        <span class="ticket-badge ${statusClass}">${ticketData.status}</span>
      </div>
      <div><strong>Category:</strong> ${ticketData.category}</div>
      <div><strong>Location/Room:</strong> ${ticketData.room_number}</div>
      <div><strong>Assigned To:</strong> ${ticketData.assigned_to}</div>
      ${ticketData.resolution_notes ? `<div><strong>Notes:</strong> ${ticketData.resolution_notes}</div>` : ""}
    `;
    contentDiv.appendChild(card);
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);

  // Auto scroll to bottom
  container.scrollTop = container.scrollHeight;
}

function getStatusBadgeClass(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("resolve")) return "badge-resolved";
  if (s.includes("progress")) return "badge-in-progress";
  return "badge-pending";
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  appendMessage("user", message);
  chatHistory.push({ role: "user", content: message });

  // Show typing loader
  const typingId = showTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        chat_history: chatHistory
      })
    });

    removeTypingIndicator(typingId);

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    appendMessage("bot", data.reply, data.ticket);
    chatHistory.push({ role: "assistant", content: data.reply });

    // If ticket was created, refresh sidebar tickets
    if (data.ticket) {
      loadRecentTickets();
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendMessage("bot", "⚠️ Sorry, could not reach the hostel server. Please ensure the backend is running.");
    console.error(err);
  }
}

function sendQuickPrompt(promptText) {
  const input = document.getElementById("userInput");
  input.value = promptText;
  document.getElementById("chatForm").dispatchEvent(new Event("submit", { cancelable: true }));
}

function showTypingIndicator() {
  const container = document.getElementById("messagesArea");
  const id = "typing-" + Date.now();
  const typingDiv = document.createElement("div");
  typingDiv.id = id;
  typingDiv.className = "message bot-message";
  typingDiv.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="message-content" style="color: #64748b; font-style: italic;">
      Typing...
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

async function loadRecentTickets() {
  const listEl = document.getElementById("ticketsList");
  try {
    const res = await fetch(`${API_BASE}/api/complaints`);
    if (!res.ok) return;
    const tickets = await res.json();
    
    if (!tickets || tickets.length === 0) {
      listEl.innerHTML = "<div class='subtext' style='padding: 8px;'>No complaints registered yet.</div>";
      return;
    }

    listEl.innerHTML = "";
    // Show most recent first (last 6)
    const recent = [...tickets].reverse().slice(0, 6);
    recent.forEach(t => {
      const item = document.createElement("div");
      item.className = "ticket-item";
      const badgeClass = getStatusBadgeClass(t.status);
      item.innerHTML = `
        <div class="ticket-item-header">
          <span class="ticket-room">${t.category} (${t.room_number})</span>
          <span class="ticket-badge ${badgeClass}">${t.status}</span>
        </div>
        <div class="ticket-desc">${t.description}</div>
      `;
      item.onclick = () => {
        sendQuickPrompt(`What is the status of ticket ${t.ticket_id}?`);
      };
      listEl.appendChild(item);
    });
  } catch (err) {
    listEl.innerHTML = "<div class='subtext' style='padding: 8px;'>Failed to load tickets.</div>";
  }
}

function clearChat() {
  const container = document.getElementById("messagesArea");
  container.innerHTML = `
    <div class="message bot-message">
      <div class="avatar">🤖</div>
      <div class="message-content">
        <p>Chat cleared! How can I help you regarding hostel rules, mess food, hot water, or reporting complaints?</p>
      </div>
    </div>
  `;
  chatHistory = [];
}
