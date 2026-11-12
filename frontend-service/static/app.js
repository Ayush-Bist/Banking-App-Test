let userProfile = null;
let allProducts = [];
let activeCategory = "All";

const PAGE_META = {
  dashboard: ["Overview Dashboard", "Real-time account telemetry powered by 5 microservices"],
  catalog: ["Products & Smart Search", "Weighted relevance ranking via Search Microservice"],
  recommendations: ["AI Advisor & MySQL Audit", "Personalized scoring backed by relational MySQL audit logs"],
  ledger: ["Transfers & MongoDB Ledger", "Live funds transfer and MongoDB document persistence"],
};

function showToast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3200);
}

// Multi-Page Navigation
function navigateTo(pageId) {
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });
  document.querySelectorAll(".page").forEach(sec => {
    sec.classList.toggle("active", sec.id === `page-${pageId}`);
  });
  document.getElementById("pageTitle").textContent = PAGE_META[pageId][0];
  document.getElementById("pageSubtitle").textContent = PAGE_META[pageId][1];

  if (pageId === "dashboard") loadDashboard();
  if (pageId === "catalog") performSearch(document.getElementById("searchInput").value);
  if (pageId === "recommendations") { loadRecommendations(); loadMySqlHistory(); }
  if (pageId === "ledger") loadLedgerData();
}

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => navigateTo(btn.dataset.page));
});

// Live Cluster Health Sidebar
async function refreshClusterHealth() {
  try {
    const res = await fetch("/api/system-status");
    const data = await res.json();
    const labels = {
      core_banking_mongodb: "Core + MongoDB",
      search_service: "Search Service",
      recommendations_mysql: "Recs + MySQL",
      chatbot_service: "AI Chatbot",
    };
    document.getElementById("healthList").innerHTML = Object.entries(labels).map(([key, label]) => {
      const ok = data[key]?.status === "healthy";
      return `<div class="health-row"><span>${label}</span><span class="${ok ? "dot-ok" : "dot-off"}">${ok ? "● UP" : "● DOWN"}</span></div>`;
    }).join("");
  } catch {
    document.getElementById("healthList").textContent = "Gateway offline";
  }
}

// Page 1: Dashboard
async function loadDashboard() {
  const [profRes, prodRes] = await Promise.all([fetch("/api/profile"), fetch("/api/search")]);
  userProfile = await profRes.json();
  const prodData = await prodRes.json();
  allProducts = prodData.results;

  const formattedBal = `$${userProfile.account_balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
  document.getElementById("topUserName").textContent = userProfile.name;
  document.getElementById("topAccountNum").textContent = userProfile.account_number;
  document.getElementById("topBalance").textContent = formattedBal;
  document.getElementById("dashBalance").textContent = formattedBal;
  document.getElementById("dashEnrolledCount").textContent = userProfile.existing_products.length;

  const maxSpend = Math.max(...Object.values(userProfile.monthly_spending), 1);
  document.getElementById("spendingBars").innerHTML = Object.entries(userProfile.monthly_spending).map(([cat, amt]) => `
    <div class="spend-item">
      <div class="spend-top"><span>${cat}</span><span>$${amt}</span></div>
      <div class="bar-bg"><div class="bar-fill" style="width:${(amt / maxSpend) * 100}%"></div></div>
    </div>
  `).join("");

  const owned = allProducts.filter(p => userProfile.existing_products.includes(p.id));
  document.getElementById("enrolledProductsList").innerHTML = owned.map(p => `
    <div class="list-row">
      <div><strong>${p.name}</strong><div class="muted">${p.category}</div></div>
      <span class="balance-chip">${p.apy}</span>
    </div>
  `).join("") || "<p class='muted'>No products enrolled yet.</p>";
}

// Page 2: Smart Search & Enrollment
async function performSearch(query = "") {
  if (!userProfile) await loadDashboard();
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const data = await res.json();

  const filtered = activeCategory === "All"
    ? data.results
    : data.results.filter(p => p.category === activeCategory);

  document.getElementById("resultCount").textContent = filtered.length;
  document.getElementById("searchResults").innerHTML = filtered.map(item => {
    const isOwned = userProfile.existing_products.includes(item.id);
    return `
      <div class="card">
        <div>
          <span class="card-tag">${item.category}</span>
          <h4>${item.name}</h4>
          <div class="card-rate">${item.apy}</div>
          <p>${item.description}</p>
        </div>
        ${isOwned
          ? `<button class="btn-enrolled" disabled>✓ Enrolled in MongoDB</button>`
          : `<button class="btn-primary" onclick="enrollProduct('${item.id}')">Apply & Enroll</button>`}
      </div>
    `;
  }).join("") || "<p class='muted'>No matching products in this category.</p>";

  document.getElementById("searchSuggestions").innerHTML = data.suggestions.map(s =>
    `<span class="suggestion-pill" onclick="applySuggestion('${s}')">${s}</span>`
  ).join("");
}

function applySuggestion(term) {
  document.getElementById("searchInput").value = term;
  performSearch(term);
}

async function enrollProduct(productId) {
  const res = await fetch("/api/enroll", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId }),
  });
  if (res.ok) {
    const data = await res.json();
    showToast(`Enrolled in ${data.product_name} (Saved to MongoDB)`);
    await loadDashboard();
    performSearch(document.getElementById("searchInput").value);
  }
}

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    activeCategory = tab.dataset.cat;
    performSearch(document.getElementById("searchInput").value);
  });
});

document.getElementById("searchBtn").addEventListener("click", () => performSearch(document.getElementById("searchInput").value));
document.getElementById("searchInput").addEventListener("input", e => performSearch(e.target.value));

// Page 3: AI Recommendations & MySQL Audit Table
async function loadRecommendations() {
  const res = await fetch("/api/recommendations");
  const data = await res.json();
  document.getElementById("mysqlBadge").textContent = data.database;
  document.getElementById("dashRecCount").textContent = data.recommendations.length;

  document.getElementById("recommendationsGrid").innerHTML = data.recommendations.map(rec => `
    <div class="card">
      <div>
        <div class="match-banner">✨ ${rec.match_score}% Match — ${rec.reason}</div>
        <span class="card-tag">${rec.category}</span>
        <h4>${rec.name}</h4>
        <div class="card-rate">${rec.apy}</div>
        <p>${rec.description}</p>
      </div>
      <button class="btn-primary" onclick="acceptOffer('${rec.id}')">Accept Offer (Log in MySQL)</button>
    </div>
  `).join("") || "<p class='muted'>You have accepted all top recommendations!</p>";
}

async function acceptOffer(productId) {
  const res = await fetch("/api/recommendations/accept", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId }),
  });
  if (res.ok) {
    showToast("Offer accepted! MySQL status updated to ACCEPTED & enrolled in MongoDB.");
    await loadDashboard();
    await loadRecommendations();
    await loadMySqlHistory();
  }
}

async function loadMySqlHistory() {
  const res = await fetch("/api/recommendations/history");
  const data = await res.json();
  document.getElementById("mysqlHistoryBody").innerHTML = data.records.map(r => `
    <tr>
      <td>#${r.id}</td>
      <td><strong>${r.product_name}</strong></td>
      <td>${r.match_score}%</td>
      <td>${r.reason}</td>
      <td><span class="status-pill ${r.status}">${r.status}</span></td>
      <td>${r.created_at}</td>
    </tr>
  `).join("");
}

// Page 4: Transfers & MongoDB Ledger
async function loadLedgerData() {
  const [txRes, chatRes] = await Promise.all([fetch("/api/transactions"), fetch("/api/chat-logs")]);
  const txs = await txRes.json();
  const chats = await chatRes.json();

  document.getElementById("mongoTxBody").innerHTML = txs.map(t => `
    <tr>
      <td><code>${t.tx_id}</code></td>
      <td><strong>${t.recipient}</strong></td>
      <td>${t.category}</td>
      <td style="color:${t.type === "CREDIT" ? "#059669" : "#dc2626"};font-weight:700">
        ${t.type === "CREDIT" ? "+" : "-"}$${t.amount.toFixed(2)}
      </td>
      <td>${t.timestamp}</td>
    </tr>
  `).join("");

  document.getElementById("mongoChatLogs").innerHTML = chats.map(c => `
    <div class="list-row">
      <div><strong>You:</strong> ${c.user_message}<br/><span class="muted"><strong>ApexAI:</strong> ${c.bot_reply}</span></div>
      <span class="tag-pill">${c.timestamp || "Logged"}</span>
    </div>
  `).join("") || "<p class='muted'>Open the AI Advisor widget to chat—conversations save automatically to MongoDB.</p>";
}

document.getElementById("transferForm").addEventListener("submit", async e => {
  e.preventDefault();
  const recipient = document.getElementById("txRecipient").value.trim();
  const category = document.getElementById("txCategory").value;
  const amount = parseFloat(document.getElementById("txAmount").value);

  const res = await fetch("/api/transfers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipient, category, amount }),
  });

  if (res.ok) {
    document.getElementById("transferForm").reset();
    showToast(`Transferred $${amount.toFixed(2)} to ${recipient} (Updated MongoDB)`);
    await loadDashboard();
    await loadLedgerData();
  } else {
    const err = await res.json();
    showToast(`Error: ${err.detail}`);
  }
});

// Chatbot Widget
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
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  appendMessage(data.reply, "bot");
  chatQuickActions.innerHTML = data.suggested_actions.map(act =>
    `<button type="button" class="quick-btn" onclick="sendChatMessage('${act}')">${act}</button>`
  ).join("");

  // Refresh MongoDB chat logs live
  loadLedgerData();
}

chatForm.addEventListener("submit", e => {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = "";
  sendChatMessage(msg);
});

// Boot Sequence
(async function init() {
  refreshClusterHealth();
  setInterval(refreshClusterHealth, 10000);
  await loadDashboard();
  await loadRecommendations();
})();