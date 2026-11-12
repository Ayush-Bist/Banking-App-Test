const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const searchResults = document.getElementById("searchResults");
const resultCount = document.getElementById("resultCount");
const searchSuggestions = document.getElementById("searchSuggestions");
const recommendationsGrid = document.getElementById("recommendationsGrid");

async function performSearch(query = "") {
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const data = await res.json();

  resultCount.textContent = data.count;
  searchResults.innerHTML = data.results.map(item => `
    <div class="card">
      <div>
        <span class="card-tag">${item.category}</span>
        <h3>${item.name}</h3>
        <div class="card-rate">${item.apy}</div>
        <p>${item.description}</p>
      </div>
      <small>Risk Level: ${item.risk_level}</small>
    </div>
  `).join("") || "<p>No matching products found.</p>";

  searchSuggestions.innerHTML = data.suggestions.map(s =>
    `<span class="suggestion-pill" onclick="triggerSuggestion('${s}')">${s}</span>`
  ).join("");
}

function triggerSuggestion(term) {
  searchInput.value = term;
  performSearch(term);
}

async function loadRecommendations() {
  const res = await fetch("/api/recommendations");
  const data = await res.json();

  document.getElementById("userName").textContent = data.user;
  document.getElementById("userBalance").textContent = `$${data.balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;

  recommendationsGrid.innerHTML = data.recommendations.map(rec => `
    <div class="card">
      <div>
        <div class="match-banner">✨ ${rec.match_score}% Match — ${rec.reason}</div>
        <span class="card-tag">${rec.category}</span>
        <h3>${rec.name}</h3>
        <div class="card-rate">${rec.apy}</div>
        <p>${rec.description}</p>
      </div>
    </div>
  `).join("");
}

// Chatbot Interactions
const chatToggle = document.getElementById("chatToggle");
const chatWindow = document.getElementById("chatWindow");
const chatClose = document.getElementById("chatClose");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const chatQuickActions = document.getElementById("chatQuickActions");

chatToggle.addEventListener("click", () => chatWindow.classList.toggle("hidden"));
chatClose.addEventListener("click", () => chatWindow.classList.add("hidden"));

function appendMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChatMessage(message) {
  appendMessage(message, "user");
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });
  const data = await res.json();
  appendMessage(data.reply, "bot");

  chatQuickActions.innerHTML = data.suggested_actions.map(act =>
    `<button type="button" class="quick-btn" onclick="sendChatMessage('${act}')">${act}</button>`
  ).join("");
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = "";
  sendChatMessage(msg);
});

searchBtn.addEventListener("click", () => performSearch(searchInput.value));
searchInput.addEventListener("input", () => performSearch(searchInput.value));

// Initial Load
performSearch();
loadRecommendations();