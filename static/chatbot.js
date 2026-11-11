(() => {
  const panel = document.getElementById("me-chat-panel");
  const toggle = document.getElementById("me-chat-toggle");
  const close = document.getElementById("me-chat-close");
  const form = document.getElementById("me-chat-form");
  const input = document.getElementById("me-chat-input");
  const send = document.getElementById("me-chat-send");
  const messages = document.getElementById("me-chat-messages");
  if (!panel || !form) return;

  function addMessage(role, text, extra = "") {
    const item = document.createElement("div");
    item.className = "me-chat-bubble " + role + (extra ? " " + extra : "");
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }
  function showPanel() {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    input.focus();
  }
  toggle.addEventListener("click", () => panel.hidden ? showPanel() : (panel.hidden = true));
  close.addEventListener("click", () => { panel.hidden = true; toggle.focus(); });

  async function loadHistory() {
    try {
      const response = await fetch("/api/chat/history", {credentials:"same-origin"});
      if (!response.ok) return;
      const data = await response.json();
      if (Array.isArray(data.messages) && data.messages.length) {
        messages.replaceChildren();
        data.messages.forEach(m => {
          if (m.role === "user" || m.role === "assistant") addMessage(m.role, m.content);
        });
      }
    } catch (error) { console.warn("Chat history unavailable", error); }
  }
  loadHistory();

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMessage("user", message);
    input.value = "";
    send.disabled = true;
    const pending = addMessage("assistant", "Thinking…");
    try {
      const response = await fetch("/api/chat", {
        method:"POST",
        credentials:"same-origin",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message})
      });
      const data = await response.json().catch(() => ({}));
      pending.remove();
      if (!response.ok) {
        addMessage("error", data.error || "Sorry, I couldn't respond just now.");
      } else {
        addMessage("assistant", data.reply || "I couldn't create a reply. Please try again.");
      }
    } catch (error) {
      pending.remove();
      addMessage("error", "Connection issue. Please check your internet and try again.");
    } finally {
      send.disabled = false;
      input.focus();
    }
  });
})();