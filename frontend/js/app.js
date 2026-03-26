const API = window.location.origin;
const LIMIT = 10;
let currentPage = 0;

// ── DOM Elements ────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const orderForm = $("#order-form");
const toggleFormBtn = $("#toggle-form");
const formHeader = $(".form-header");
const itemsContainer = $("#items-container");
const addItemBtn = $("#add-item");
const totalValue = $("#total-value");
const ordersTbody = $("#orders-tbody");
const pagination = $("#pagination");
const refreshBtn = $("#refresh-orders");
const modalOverlay = $("#modal-overlay");
const modalBody = $("#modal-body");
const modalClose = $("#modal-close");
const navToggle = $("#nav-toggle");
const navLinks = $("#nav-links");
const toastContainer = $("#toast-container");

// ── Init ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadOrders();
  setupEventListeners();
  setupScrollSpy();
});

// ── Event Listeners ─────────────────────────────────────────────
function setupEventListeners() {
  // Toggle form
  formHeader.addEventListener("click", () => {
    orderForm.classList.toggle("collapsed");
    toggleFormBtn.querySelector("svg").style.transform =
      orderForm.classList.contains("collapsed") ? "" : "rotate(180deg)";
  });

  // Add item row
  addItemBtn.addEventListener("click", addItemRow);

  // Calculate total on input
  itemsContainer.addEventListener("input", calculateTotal);

  // Submit order
  orderForm.addEventListener("submit", handleCreateOrder);

  // Refresh
  refreshBtn.addEventListener("click", () => loadOrders());

  // Modal close
  modalClose.addEventListener("click", closeModal);
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  // Mobile nav toggle
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });

  // Close mobile nav on link click
  $$(".nav-link").forEach((link) => {
    link.addEventListener("click", () => navLinks.classList.remove("open"));
  });

  // Remove initial item row button
  itemsContainer.addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-remove-item")) {
      const rows = itemsContainer.querySelectorAll(".item-row");
      if (rows.length > 1) {
        e.target.closest(".item-row").remove();
        calculateTotal();
      }
    }
  });
}

// ── Scroll Spy ──────────────────────────────────────────────────
function setupScrollSpy() {
  const sections = ["hero", "about", "news", "orders"];
  window.addEventListener("scroll", () => {
    const scrollPos = window.scrollY + 100;
    sections.forEach((id) => {
      const section = document.getElementById(id);
      if (section) {
        const top = section.offsetTop;
        const height = section.offsetHeight;
        const link = $(`.nav-link[data-section="${id}"]`);
        if (link) {
          if (scrollPos >= top && scrollPos < top + height) {
            $$(".nav-link").forEach((l) => l.classList.remove("active"));
            link.classList.add("active");
          }
        }
      }
    });
  });
}

// ── Add Item Row ────────────────────────────────────────────────
function addItemRow() {
  const row = document.createElement("div");
  row.className = "item-row";
  row.innerHTML = `
        <input type="text" placeholder="Nome do item" class="item-nome" required>
        <input type="number" placeholder="Preço (R$)" class="item-preco" min="0" step="0.01" required>
        <button type="button" class="btn-remove-item" title="Remover item">✕</button>
    `;
  itemsContainer.appendChild(row);
}

// ── Calculate Total ─────────────────────────────────────────────
function calculateTotal() {
  let total = 0;
  itemsContainer.querySelectorAll(".item-row").forEach((row) => {
    const price = parseFloat(row.querySelector(".item-preco").value) || 0;
    total += price;
  });
  totalValue.textContent = formatCurrency(total);
}

// ── Create Order ────────────────────────────────────────────────
async function handleCreateOrder(e) {
  e.preventDefault();

  const nomeCliente = $("#nome_cliente").value.trim();
  if (!nomeCliente) return toast("Informe o nome do cliente", "error");

  const items = [];
  let valid = true;
  itemsContainer.querySelectorAll(".item-row").forEach((row) => {
    const name = row.querySelector(".item-nome").value.trim();
    const price = parseFloat(row.querySelector(".item-preco").value);
    if (!name || !price) {
      valid = false;
      return;
    }
    items.push({ name, price });
  });

  if (!valid || items.length === 0)
    return toast("Preencha todos os campos dos itens", "error");

  try {
    const res = await fetch(`${API}/pedidos/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name_client: nomeCliente, items }),
    });

    if (!res.ok) throw new Error("Erro ao criar pedido");

    toast("Pedido criado com sucesso!", "success");
    orderForm.reset();
    // Keep one item row
    itemsContainer.innerHTML = `
            <div class="item-row">
                <input type="text" placeholder="Nome do item" class="item-nome" required>
                <input type="number" placeholder="Preço (R$)" class="item-preco" min="0" step="0.01" required>
                <button type="button" class="btn-remove-item" title="Remover item">✕</button>
            </div>
        `;
    totalValue.textContent = "R$ 0,00";
    currentPage = 0;
    loadOrders();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Load Orders ─────────────────────────────────────────────────
async function loadOrders() {
  try {
    const skip = currentPage * LIMIT;
    const res = await fetch(`${API}/pedidos/?skip=${skip}&limit=${LIMIT}`);
    if (!res.ok) throw new Error("Erro ao carregar pedidos");

    const data = await res.json();
    renderOrders(data.orders);
    renderPagination(data.total, data.skip, data.limit);
    updateStats(data);
  } catch (err) {
    console.error(err);
    toast("Não foi possível carregar os pedidos", "error");
  }
}

// ── Render Orders ───────────────────────────────────────────────
function renderOrders(pedidos) {
  if (!pedidos || pedidos.length === 0) {
    ordersTbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="6">
                    <div class="empty-state">
                        <span class="empty-icon">📦</span>
                        <p>Nenhum pedido encontrado</p>
                        <small>Crie um novo pedido usando o formulário acima</small>
                    </div>
                </td>
            </tr>`;
    return;
  }

  ordersTbody.innerHTML = pedidos
    .map(
      (p) => `
        <tr>
            <td><strong>${escapeHtml(p.name_client)}</strong></td>
            <td>${p.items.length} ${p.items.length === 1 ? "item" : "itens"}</td>
            <td>${formatCurrency(p.value)}</td>
            <td><span class="status-badge status-${p.status}">
                ${p.status === "pendente" ? "⏳" : "✅"} ${capitalize(p.status)}
            </span></td>
            <td>${formatDate(p.created_at)}</td>
            <td>
                <div class="actions-cell">
                    <button class="btn btn-sm btn-outline" onclick="viewOrder('${p.id}')">👁 Ver</button>
                    ${
                      p.status === "pendente"
                        ? `<button class="btn btn-sm btn-success" onclick="markDone('${p.id}')">✓ Concluir</button>`
                        : `<button class="btn btn-sm btn-outline" onclick="markPending('${p.id}')">↩ Pendente</button>`
                    }
                    <button class="btn btn-sm btn-danger" onclick="deleteOrder('${p.id}')">🗑</button>
                </div>
            </td>
        </tr>
    `,
    )
    .join("");
}

// ── Render Pagination ───────────────────────────────────────────
function renderPagination(total, skip, limit) {
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  const current = Math.floor(skip / limit);
  let html = "";

  html += `<button class="page-btn" ${current === 0 ? "disabled" : ""} onclick="goToPage(${current - 1})">← Anterior</button>`;

  for (let i = 0; i < totalPages; i++) {
    html += `<button class="page-btn ${i === current ? "active" : ""}" onclick="goToPage(${i})">${i + 1}</button>`;
  }

  html += `<button class="page-btn" ${current === totalPages - 1 ? "disabled" : ""} onclick="goToPage(${current + 1})">Próximo →</button>`;

  pagination.innerHTML = html;
}

// ── Update Stats ────────────────────────────────────────────────
async function updateStats(data) {
  // If we have the full listing data, use it; otherwise re-fetch all
  const totalEl = $("#stat-total");
  const pendingEl = $("#stat-pending");
  const doneEl = $("#stat-done");

  if (data) {
    totalEl.textContent = data.total;
    const pending = data.orders.filter((p) => p.status === "pendente").length;
    const done = data.orders.filter((p) => p.status === "concluido").length;
    // For accurate stats, we'd need all data; approximate from current page + total
    pendingEl.textContent = pending;
    doneEl.textContent = done;
  }

  // Fetch all to get accurate counts
  try {
    const res = await fetch(`${API}/pedidos/?skip=0&limit=1000`);
    if (res.ok) {
      const allData = await res.json();
      totalEl.textContent = allData.total;
      pendingEl.textContent = allData.orders.filter(
        (p) => p.status === "pendente",
      ).length;
      doneEl.textContent = allData.orders.filter(
        (p) => p.status === "concluido",
      ).length;
    }
  } catch (e) {
    /* ignore */
  }
}

// ── View Order Detail ───────────────────────────────────────────
async function viewOrder(id) {
  try {
    const res = await fetch(`${API}/pedidos/${id}`);
    if (!res.ok) throw new Error("Pedido não encontrado");
    const p = await res.json();

    modalBody.innerHTML = `
            <div class="detail-row"><span class="label">ID</span><span class="value" style="font-size:.78rem;word-break:break-all">${p.id}</span></div>
            <div class="detail-row"><span class="label">Cliente</span><span class="value">${escapeHtml(p.name_client)}</span></div>
            <div class="detail-row"><span class="label">Valor Total</span><span class="value" style="color:var(--accent-3)">${formatCurrency(p.value)}</span></div>
            <div class="detail-row"><span class="label">Status</span><span class="value"><span class="status-badge status-${p.status}">${p.status === "pendente" ? "⏳" : "✅"} ${capitalize(p.status)}</span></span></div>
            <div class="detail-row"><span class="label">Criado em</span><span class="value">${formatDate(p.created_at)}</span></div>
            <div class="detail-row"><span class="label">Atualizado em</span><span class="value">${formatDate(p.updated_at)}</span></div>
            <div class="modal-items">
                <h4>Itens do Pedido (${p.items.length})</h4>
                ${p.items
                  .map(
                    (item) => `
                    <div class="modal-item">
                        <div class="item-info">
                            <span>${escapeHtml(item.name)}</span>
                        </div>
                        <span>${formatCurrency(item.price)}</span>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        `;
    openModal();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Update Status ───────────────────────────────────────────────
async function markDone(id) {
  await updateStatus(id, "concluido");
}

async function markPending(id) {
  await updateStatus(id, "pendente");
}

async function updateStatus(id, status) {
  try {
    const res = await fetch(`${API}/pedidos/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Erro ao atualizar status");
    toast(`Pedido marcado como ${status}`, "success");
    loadOrders();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Delete Order ────────────────────────────────────────────────
async function deleteOrder(id) {
  if (!confirm("Tem certeza que deseja excluir este pedido?")) return;
  try {
    const res = await fetch(`${API}/pedidos/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Erro ao excluir pedido");
    toast("Pedido excluído", "info");
    loadOrders();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Pagination Nav ──────────────────────────────────────────────
function goToPage(page) {
  currentPage = page;
  loadOrders();
  document.getElementById("orders").scrollIntoView({ behavior: "smooth" });
}

// ── Modal ───────────────────────────────────────────────────────
function openModal() {
  modalOverlay.classList.add("open");
  document.body.style.overflow = "hidden";
}
function closeModal() {
  modalOverlay.classList.remove("open");
  document.body.style.overflow = "";
}

// ── Toast ───────────────────────────────────────────────────────
function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Utilities ───────────────────────────────────────────────────
function formatCurrency(v) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(v);
}

function formatDate(iso) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
