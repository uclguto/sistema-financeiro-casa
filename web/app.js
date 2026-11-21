/**
 * Casa G&J — Painel Financeiro Mobile PWA
 * Criptografia Client-Side AES-256-GCM com WebCrypto API (Zero plain-text no servidor)
 */

let appData = null;
let currentPin = "";
let currentPayloadEnc = null;

// ==============================================================================
// 1. UTILITÁRIOS CRIPTOGRÁFICOS (WEBCRYPTO API NATIVA)
// ==============================================================================

function base64ToUint8Array(base64) {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

async function derivarChaveWebCrypto(pin, saltBytes) {
  const enc = new TextEncoder();
  const pinBytes = enc.encode(pin);
  const keyMaterial = await window.crypto.subtle.importKey(
    "raw",
    pinBytes,
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  return window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: saltBytes,
      iterations: 100000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"]
  );
}

async function descriptografarPayload(pin, payloadEnc) {
  const salt = base64ToUint8Array(payloadEnc.salt);
  const iv = base64ToUint8Array(payloadEnc.iv);
  const ciphertext = base64ToUint8Array(payloadEnc.ciphertext);

  const key = await derivarChaveWebCrypto(pin, salt);
  const decryptedBuf = await window.crypto.subtle.decrypt(
    { name: "AES-GCM", iv: iv },
    key,
    ciphertext
  );

  const dec = new TextDecoder("utf-8");
  return JSON.parse(dec.decode(decryptedBuf));
}

// ==============================================================================
// 2. FORMATAÇÃO E HELPERS
// ==============================================================================

function formatMoeda(num) {
  if (num === null || num === undefined || isNaN(num)) return "R$ 0,00";
  return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// ==============================================================================
// 3. FLUXO DE DESBLOQUEIO POR PIN
// ==============================================================================

async function carregarPayloadCriptografado() {
  if (!currentPayloadEnc) {
    const res = await fetch("payload.enc.json?t=" + Date.now());
    if (!res.ok) throw new Error("Não foi possível carregar payload.enc.json");
    currentPayloadEnc = await res.json();
  }
  return currentPayloadEnc;
}

function updatePinDots() {
  const dots = document.querySelectorAll("#pin-dots .dot");
  dots.forEach((dot, idx) => {
    if (idx < currentPin.length) {
      dot.classList.add("filled");
    } else {
      dot.classList.remove("filled");
    }
  });
}

function showPinError(msg) {
  const errEl = document.getElementById("pin-error");
  errEl.textContent = msg || "PIN incorreto. Tente novamente.";
  errEl.classList.add("visible");
  const dotsEl = document.getElementById("pin-dots");
  dotsEl.style.transform = "translateX(8px)";
  setTimeout(() => (dotsEl.style.transform = "translateX(-8px)"), 100);
  setTimeout(() => (dotsEl.style.transform = "translateX(6px)"), 200);
  setTimeout(() => (dotsEl.style.transform = "translateX(0)"), 300);

  setTimeout(() => {
    currentPin = "";
    updatePinDots();
    errEl.classList.remove("visible");
  }, 1000);
}

async function tentarDesbloqueio(pin) {
  try {
    const encData = await carregarPayloadCriptografado();
    const data = await descriptografarPayload(pin, encData);
    appData = data;
    sessionStorage.setItem("casa_pin", pin);

    // Sucesso! Transição de tela
    document.getElementById("pin-modal").classList.add("hidden");
    document.getElementById("app-container").classList.remove("hidden");

    if (data.metadata && data.metadata.gerado_em) {
      const dt = new Date(data.metadata.gerado_em);
      document.getElementById("sync-info").textContent =
        "Atualizado " + dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
    }

    renderizarTudo();
  } catch (err) {
    console.warn("Falha de decifragem:", err);
    showPinError();
  }
}

function setupKeypad() {
  document.querySelectorAll(".keypad .key-btn[data-key]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (currentPin.length < 4) {
        currentPin += btn.dataset.key;
        updatePinDots();
        if (currentPin.length === 4) {
          setTimeout(() => tentarDesbloqueio(currentPin), 150);
        }
      }
    });
  });

  document.getElementById("key-clear").addEventListener("click", () => {
    currentPin = "";
    updatePinDots();
  });

  document.getElementById("key-back").addEventListener("click", () => {
    if (currentPin.length > 0) {
      currentPin = currentPin.slice(0, -1);
      updatePinDots();
    }
  });

  // Listener de teclado físico (computador)
  window.addEventListener("keydown", (e) => {
    const modal = document.getElementById("pin-modal");
    if (!modal.classList.contains("hidden")) {
      if (e.key >= "0" && e.key <= "9") {
        if (currentPin.length < 4) {
          currentPin += e.key;
          updatePinDots();
          if (currentPin.length === 4) {
            setTimeout(() => tentarDesbloqueio(currentPin), 150);
          }
        }
      } else if (e.key === "Backspace") {
        currentPin = currentPin.slice(0, -1);
        updatePinDots();
      } else if (e.key === "Escape") {
        currentPin = "";
        updatePinDots();
      }
    }
  });
}

// ==============================================================================
// 4. RENDERIZAÇÃO DAS 4 TELAS
// ==============================================================================

function renderizarTudo() {
  if (!appData) return;
  renderizarTelaAgora();
  renderizarTelaJe();
  renderizarTelaParcelas();
  renderizarTelaRaioX();
}

// ------------------------------------------------------------------------------
// TELA 1: AGORA
// ------------------------------------------------------------------------------
function renderizarTelaAgora() {
  const rmNov = appData.resumo_mensal[appData.resumo_mensal.length - 1] || {};
  const tetoGuto = appData.regras_e_tetos.teto_cartao_guto || 3500;
  const tetoJe = appData.regras_e_tetos.teto_cartao_je || 2500;

  const gastGuto = rmNov.cartao_augusto || 0;
  const gastJe = rmNov.cartao_jessica || 0;

  // Hero Card
  document.getElementById("hero-month-label").textContent = "Novembro / 2026";
  document.getElementById("hero-guto-val").textContent = formatMoeda(gastGuto);
  document.getElementById("hero-je-val").textContent = formatMoeda(gastJe);

  const pctGuto = Math.min((gastGuto / tetoGuto) * 100, 100);
  const pctJe = Math.min((gastJe / tetoJe) * 100, 100);

  const barGuto = document.getElementById("hero-guto-bar");
  barGuto.style.width = pctGuto + "%";
  barGuto.className = "progress-bar " + (pctGuto > 95 ? "danger" : pctGuto > 75 ? "warning" : "success");

  const barJe = document.getElementById("hero-je-bar");
  barJe.style.width = pctJe + "%";
  barJe.className = "progress-bar " + (pctJe > 95 ? "danger" : pctJe > 75 ? "warning" : "success");

  // Semáforo VA (Semana)
  const metaVaSem = appData.regras_e_tetos.teto_va_semanal || 630;
  // Gasto recente da semana em Novembro (estimado em ~R$ 480 da última semana auditada)
  const spentVaSem = 480.90;
  const availVaSem = Math.max(metaVaSem - spentVaSem, 0);
  const pctVa = Math.min((spentVaSem / metaVaSem) * 100, 100);

  const barVa = document.getElementById("gauge-va-bar");
  barVa.style.width = pctVa + "%";
  barVa.className = "gauge-bar " + (pctVa > 90 ? "red" : pctVa > 75 ? "yellow" : "");
  document.getElementById("sem-va-spent").textContent = formatMoeda(spentVaSem) + " gastos";
  document.getElementById("sem-va-avail").textContent = formatMoeda(availVaSem) + " livres";

  // Semáforo Comer Fora (Semana)
  const metaCfSem = appData.regras_e_tetos.teto_comer_fora_semanal || 250;
  const spentCfSem = 142.00;
  const availCfSem = Math.max(metaCfSem - spentCfSem, 0);
  const pctCf = Math.min((spentCfSem / metaCfSem) * 100, 100);

  const barCf = document.getElementById("gauge-cf-bar");
  barCf.style.width = pctCf + "%";
  barCf.className = "gauge-bar " + (pctCf > 90 ? "red" : pctCf > 75 ? "yellow" : "");
  document.getElementById("sem-cf-spent").textContent = formatMoeda(spentCfSem) + " gastos";
  document.getElementById("sem-cf-avail").textContent = formatMoeda(availCfSem) + " livres";

  // Semáforos Uber Guto e Jé
  const metaUber = 100;
  const spentUg = 68.40;
  const spentUj = 45.00;

  document.getElementById("gauge-uber-guto-bar").style.width = (spentUg / metaUber) * 100 + "%";
  document.getElementById("sem-ug-spent").textContent = formatMoeda(spentUg);
  document.getElementById("sem-ug-avail").textContent = formatMoeda(metaUber - spentUg) + " livres";

  document.getElementById("gauge-uber-je-bar").style.width = (spentUj / metaUber) * 100 + "%";
  document.getElementById("sem-uj-spent").textContent = formatMoeda(spentUj);
  document.getElementById("sem-uj-avail").textContent = formatMoeda(metaUber - spentUj) + " livres";

  // Calculadora Jé 30%
  setupCalculadoraJe();
}

function setupCalculadoraJe() {
  const inputEl = document.getElementById("calc-je-input");
  const btnEl = document.getElementById("btn-calc-je");
  const resEl = document.getElementById("calc-je-result");

  function calcular() {
    const val = parseFloat(inputEl.value);
    if (!val || val <= 0) {
      resEl.style.display = "none";
      return;
    }
    const save30 = val * 0.30;
    const free70 = val * 0.70;
    document.getElementById("calc-save-val").textContent = formatMoeda(save30);
    document.getElementById("calc-free-val").textContent = formatMoeda(free70);
    resEl.style.display = "grid";
  }

  btnEl.addEventListener("click", calcular);
  inputEl.addEventListener("input", calcular);
}

// ------------------------------------------------------------------------------
// TELA 2: JÉ & CASA
// ------------------------------------------------------------------------------
function renderizarTelaJe() {
  const potes = [
    {
      nome: "👶 Poupança Clara",
      saldo: appData.cofrinhos.poupanca_clara.saldo_atual,
      desc: "Patrimônio protegido da Clara (reposto integralmente com a PLR)",
    },
    {
      nome: "🛡️ Cofrinho Reserva Familiar",
      saldo: appData.cofrinhos.cofrinho_reserva.saldo_atual,
      desc: "Reserva emergencial (reconstruir com alívio das parcelas)",
    },
    {
      nome: "⚡ RDB Imediato Nubank",
      saldo: appData.cofrinhos.rdb_nubank.saldo_atual,
      desc: "Liquidez diária para imprevistos imediatos",
    },
    {
      nome: "⚖️ Equalizador 2x1 (Jun/2027)",
      saldo: 0.0,
      desc: "Guardar R$ 1.050/mês nos meses sim para resgatar R$ 2.100 no mês não",
    },
  ];

  const cont = document.getElementById("potes-container");
  cont.innerHTML = "";
  potes.forEach((p) => {
    const card = document.createElement("div");
    card.className = "pote-card";
    card.innerHTML = `
      <div class="pote-left">
        <span class="pote-title">${p.nome}</span>
        <span class="pote-desc">${p.desc}</span>
      </div>
      <span class="pote-val">${formatMoeda(p.saldo)}</span>
    `;
    cont.appendChild(card);
  });
}

// ------------------------------------------------------------------------------
// TELA 3: PARCELAS & CORTES
// ------------------------------------------------------------------------------
function renderizarTelaParcelas() {
  const futs = appData.parcelas_futuras || [];
  const chartCont = document.getElementById("parcelas-chart-container");
  chartCont.innerHTML = "";

  const maxVal = Math.max(...futs.map((f) => f.total_parcelas), 1764.16);

  futs.forEach((f) => {
    const col = document.createElement("div");
    col.className = "chart-bar-col";
    const heightPct = Math.max((f.total_parcelas / maxVal) * 100, 5);
    const isLow = f.total_parcelas < 500;
    col.innerHTML = `
      <div class="chart-bar ${isLow ? "low" : ""}" style="height: ${heightPct}%;" title="${f.mes}: ${formatMoeda(f.total_parcelas)}"></div>
      <span class="chart-label">${f.mes.slice(5)}</span>
    `;
    chartCont.appendChild(col);
  });

  // Checklist de Cortes LocalStorage
  setupChecklistCortes();
}

function setupChecklistCortes() {
  const chks = document.querySelectorAll(".chk-cut");
  const savingsEl = document.getElementById("total-savings");

  function recalcular() {
    let tot = 0;
    chks.forEach((chk) => {
      const savedState = localStorage.getItem("chk_" + chk.id);
      if (savedState === "true") {
        chk.checked = true;
      }
      if (chk.checked) {
        tot += parseFloat(chk.dataset.save || 0);
      }
    });
    savingsEl.textContent = formatMoeda(tot) + "/mês";
  }

  chks.forEach((chk) => {
    chk.addEventListener("change", () => {
      localStorage.setItem("chk_" + chk.id, chk.checked);
      recalcular();
    });
  });

  recalcular();
}

// ------------------------------------------------------------------------------
// TELA 4: RAIO-X 2026
// ------------------------------------------------------------------------------
function renderizarTelaRaioX() {
  const meses = appData.resumo_mensal || [];
  const cont = document.getElementById("raiox-container");
  cont.innerHTML = "";

  meses.slice().reverse().forEach((m) => {
    const card = document.createElement("div");
    card.className = "month-card";
    card.innerHTML = `
      <div class="month-card-header">
        <span>${m.mes}</span>
        <span class="${m.saldo_jessica_final >= 0 ? "text-success" : "text-muted"}">
          ${formatMoeda(m.salario_liquido + m.jessica_repasses_liquido)}
        </span>
      </div>
      <div class="month-details-grid">
        <div class="month-row"><span>Salário Líq Guto:</span> <strong>${formatMoeda(m.salario_liquido)}</strong></div>
        <div class="month-row"><span>Repasses Jéssica:</span> <strong>${formatMoeda(m.jessica_repasses_liquido)}</strong></div>
        <div class="month-row"><span>Cartões Guto:</span> <strong>${formatMoeda(m.cartao_augusto)}</strong></div>
        <div class="month-row"><span>Cartões Jéssica:</span> <strong>${formatMoeda(m.cartao_jessica)}</strong></div>
        <div class="month-row"><span>Colégio Clara:</span> <strong>${formatMoeda(m.colegio_clara)}</strong></div>
        <div class="month-row"><span>Boletos Casa:</span> <strong>${formatMoeda(m.boletos_casa)}</strong></div>
      </div>
    `;
    cont.appendChild(card);
  });
}

// ==============================================================================
// 5. NAVEGAÇÃO ENTRE ABAS
// ==============================================================================

function setupNavigation() {
  const navBtns = document.querySelectorAll(".app-nav .nav-item");
  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      navBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const targetTabId = btn.dataset.tab;
      document.querySelectorAll(".tab-pane").forEach((pane) => {
        pane.classList.remove("active");
      });
      document.getElementById(targetTabId).classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  // Botão Bloquear
  document.getElementById("btn-lock").addEventListener("click", () => {
    sessionStorage.removeItem("casa_pin");
    appData = null;
    currentPin = "";
    updatePinDots();
    document.getElementById("app-container").classList.add("hidden");
    document.getElementById("pin-modal").classList.remove("hidden");
  });

  // Botão Tema Claro/Escuro
  const btnTheme = document.getElementById("btn-theme");
  const savedTheme = localStorage.getItem("casa_theme");
  if (savedTheme === "light") {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
  }

  btnTheme.addEventListener("click", () => {
    if (document.body.classList.contains("light-theme")) {
      document.body.classList.remove("light-theme");
      document.body.classList.add("dark-theme");
      localStorage.setItem("casa_theme", "dark");
    } else {
      document.body.classList.remove("dark-theme");
      document.body.classList.add("light-theme");
      localStorage.setItem("casa_theme", "light");
    }
  });
}

// ==============================================================================
// 6. INICIALIZAÇÃO
// ==============================================================================

window.addEventListener("DOMContentLoaded", async () => {
  setupKeypad();
  setupNavigation();

  // Registrar Service Worker para PWA
  if ("serviceWorker" in navigator) {
    try {
      await navigator.serviceWorker.register("sw.js");
      console.log("Service Worker PWA registrado com sucesso!");
    } catch (e) {
      console.log("Service Worker não registrado:", e);
    }
  }

  // Tenta auto-desbloqueio se sessão já aberta
  const savedPin = sessionStorage.getItem("casa_pin");
  if (savedPin) {
    tentarDesbloqueio(savedPin);
  }
});
