const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const welcome = document.getElementById("welcome");
const memoryList = document.getElementById("memoryList");
const memoryCount = document.getElementById("memoryCount");

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(role, content, options = {}) {
  if (welcome && welcome.isConnected) welcome.remove();
  const wrap = document.createElement("div");
  wrap.className = `message ${role}`;
  if (options.typing) wrap.classList.add("typing-message");

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "assistant" ? "d" : "you";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;
  if (options.typing) bubble.classList.add("typing");

  wrap.append(avatar, bubble);
  messagesEl.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const history = await response.json();
    if (history.length) {
      if (welcome && welcome.isConnected) welcome.remove();
      history.forEach(item => addMessage(item.role, item.content));
    }
  } catch (error) {
    console.error("Could not load history", error);
  }
}

async function loadMemories() {
  try {
    const response = await fetch("/api/memories");
    const memories = await response.json();
    memoryCount.textContent = memories.length;
    memoryList.replaceChildren();
    memories.forEach(memory => {
      const li = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = memory.content;
      const del = document.createElement("button");
      del.className = "delete-memory";
      del.textContent = "×";
      del.title = "Delete this memory";
      del.setAttribute("aria-label", "Delete memory");
      del.addEventListener("click", async () => {
        const result = await fetch(`/api/memories/${memory.id}`, { method: "DELETE" });
        if (result.ok) loadMemories();
      });
      li.append(text, del);
      memoryList.appendChild(li);
    });
  } catch (error) {
    console.error("Could not load memories", error);
  }
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return;
  addMessage("user", trimmed);
  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;
  const typing = addMessage("assistant", "Diya is thinking...", { typing: true });

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed })
    });
    const data = await response.json();
    typing.remove();
    if (!response.ok) {
      addMessage("assistant", data.error || "Something went wrong. Please try again.");
    } else {
      addMessage("assistant", data.reply);
      if (trimmed.toLowerCase().startsWith("remember:")) loadMemories();
    }
  } catch (error) {
    typing.remove();
    addMessage("assistant", "I couldn't connect to the app server. Check that Flask is running, then try again.");
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
});

document.querySelectorAll(".suggestion").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.textContent));
});


document.getElementById("clearBtn").addEventListener("click", async () => {
  if (!confirm("Delete all chat history? Saved memories will remain.")) {
    return;
  }

  try {
    const response = await fetch("/api/history", {
      method: "DELETE"
    });

    if (!response.ok) {
      alert("Could not clear chat history. Please try again.");
      return;
    }

    messagesEl.replaceChildren();

    const welcomeCard = document.createElement("div");
    welcomeCard.className = "welcome";
    welcomeCard.id = "welcome";

    const flower = document.createElement("div");
    flower.className = "welcome-flower";
    flower.textContent = "✿";

    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "A LITTLE SPACE JUST FOR YOU";

    const heading = document.createElement("h2");
    heading.append("Welcome back ");

    const heart = document.createElement("span");
    heart.textContent = "♡";
    heading.appendChild(heart);

    const copy = document.createElement("p");
    copy.className = "welcome-copy";
    copy.textContent =
      "Your chat history is cleared. I'm ready for a fresh conversation.";

    welcomeCard.append(flower, eyebrow, heading, copy);
    messagesEl.appendChild(welcomeCard);
  } catch (error) {
    console.error("Could not clear chat history:", error);
    alert("Could not connect to the app server.");
  }
});


document.getElementById("newChatBtn")?.addEventListener("click", async () => {
  if (!confirm("Start a fresh conversation by clearing chat history? Saved memories will remain.")) return;
  const response = await fetch("/api/history", { method: "DELETE" });
  if (response.ok) location.reload();
});

loadHistory();
loadMemories();
