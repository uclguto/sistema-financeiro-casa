/**
 * Casa G&J — Painel Financeiro Mobile & Desktop PWA
 * Criptografia Client-Side AES-256-GCM com WebCrypto API nativa (Zero plain-text no servidor)
 * 28 Categorias Completas, Filtro por Mês, Busca Instantânea e Drill-Down de Transações
 */

let appData = null;
let currentPin = "";
let currentPayloadEnc = null;
let currentViewMode = "ranking"; // "ranking" ou "matriz"

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
// 4. RENDERIZAÇÃO GERAL
// ==============================================================================

function renderizarTudo() {
  if (!appData) return;
  renderizarTelaAgora();
  renderizarTelaJe();
  renderizarTelaParcelas();
  renderizarTelaRaioX();
}

// ==============================================================================
// TELA 1: AGORA (DADOS 100% REAIS + GASTOS RÁPIDOS NO LOCALSTORAGE)
// ==============================================================================

function getQuickExpenses() {
  try {
    return JSON.parse(localStorage.getItem("casa_quick_expenses") || "[]");
  } catch (e) {
    return [];
  }
}

function saveQuickExpenses(list) {
  localStorage.setItem("casa_quick_expenses", JSON.stringify(list));
}

function renderizarTelaAgora() {
  const sem = appData.semaforos_atuais || {};
  const tetos = appData.regras_e_tetos || {};
  const quickList = getQuickExpenses();

  // Soma gastos manuais rápidos desta semana
  const quickTotals = {
    va: 0,
    comer_fora: 0,
    uber_guto: 0,
    uber_je: 0,
    compras_online: 0,
    outro: 0,
  };
  quickList.forEach((item) => {
    if (quickTotals[item.cat] !== undefined) {
      quickTotals[item.cat] += item.val;
    }
  });

  // 1. Termômetro Cartões do Mês (Novembro/2026)
  const tetoGuto = tetos.teto_cartao_guto || 3500;
  const tetoJe = tetos.teto_cartao_je || 2500;
  const gastGuto = (sem.cartao_guto_mes || 0) + quickTotals.uber_guto;
  const gastJe = (sem.cartao_je_mes || 0) + quickTotals.uber_je;

  document.getElementById("hero-month-label").textContent = "Novembro / 2026";
  document.getElementById("hero-guto-val").textContent = formatMoeda(gastGuto);
  document.getElementById("hero-je-val").textContent = formatMoeda(gastJe);

  const pctGuto = Math.min((gastGuto / tetoGuto) * 100, 100);
  const pctJe = Math.min((gastJe / tetoJe) * 100, 100);

  const barGuto = document.getElementById("hero-guto-bar");
  barGuto.style.width = pctGuto + "%";
  barGuto.className = "progress-bar " + (pctGuto > 95 ? "danger" : pctGuto > 80 ? "warning" : "success");
  const statGuto = document.getElementById("hero-guto-status");
  statGuto.textContent = pctGuto > 100 ? "Acima do teto" : `${pctGuto.toFixed(0)}% do teto`;
  statGuto.className = "val-status " + (pctGuto > 95 ? "danger" : pctGuto > 80 ? "warning" : "ok");

  const barJe = document.getElementById("hero-je-bar");
  barJe.style.width = pctJe + "%";
  barJe.className = "progress-bar " + (pctJe > 95 ? "danger" : pctJe > 80 ? "warning" : "success");
  const statJe = document.getElementById("hero-je-status");
  statJe.textContent = pctJe > 100 ? "Acima do teto" : `${pctJe.toFixed(0)}% do teto`;
  statJe.className = "val-status " + (pctJe > 95 ? "danger" : pctJe > 80 ? "warning" : "ok");

  // 2. Semáforo Vale-Alimentação (Semana)
  const metaVaSem = tetos.teto_va_semanal || 630;
  const spentVaSem = (sem.va_semana || 0) + quickTotals.va;
  const availVaSem = Math.max(metaVaSem - spentVaSem, 0);
  const pctVa = Math.min((spentVaSem / metaVaSem) * 100, 100);

  const barVa = document.getElementById("gauge-va-bar");
  barVa.style.width = pctVa + "%";
  barVa.className = "gauge-bar " + (pctVa > 90 ? "red" : pctVa > 75 ? "yellow" : "");
  document.getElementById("sem-va-spent").textContent = formatMoeda(spentVaSem) + " gastos";
  const elVaAvail = document.getElementById("sem-va-avail");
  elVaAvail.textContent = formatMoeda(availVaSem) + " livres";
  elVaAvail.className = "sem-avail " + (availVaSem <= 0 ? "danger" : "");

  // 3. Semáforo Comer Fora & Lazer
  const metaCfSem = tetos.teto_comer_fora_semanal || 250;
  const spentCfSem = (sem.comer_fora_semana || 0) + quickTotals.comer_fora;
  const availCfSem = Math.max(metaCfSem - spentCfSem, 0);
  const pctCf = Math.min((spentCfSem / metaCfSem) * 100, 100);

  const barCf = document.getElementById("gauge-cf-bar");
  barCf.style.width = pctCf + "%";
  barCf.className = "gauge-bar " + (pctCf > 90 ? "red" : pctCf > 75 ? "yellow" : "");
  document.getElementById("sem-cf-spent").textContent = formatMoeda(spentCfSem) + " gastos";
  const elCfAvail = document.getElementById("sem-cf-avail");
  elCfAvail.textContent = formatMoeda(availCfSem) + " livres";
  elCfAvail.className = "sem-avail " + (availCfSem <= 0 ? "danger" : "");

  // 4. Uber Guto
  const metaUg = tetos.teto_uber_guto_semanal || 100;
  const spentUg = (sem.uber_guto_semana || 0) + quickTotals.uber_guto;
  const availUg = Math.max(metaUg - spentUg, 0);
  const pctUg = Math.min((spentUg / metaUg) * 100, 100);
  const barUg = document.getElementById("gauge-uber-guto-bar");
  barUg.style.width = pctUg + "%";
  barUg.className = "gauge-bar " + (pctUg > 90 ? "red" : pctUg > 75 ? "yellow" : "");
  document.getElementById("sem-ug-spent").textContent = formatMoeda(spentUg);
  document.getElementById("sem-ug-avail").textContent = formatMoeda(availUg) + " livres";

  // 5. Uber Jéssica
  const metaUj = tetos.teto_uber_je_semanal || 100;
  const spentUj = (sem.uber_je_semana || 0) + quickTotals.uber_je;
  const availUj = Math.max(metaUj - spentUj, 0);
  const pctUj = Math.min((spentUj / metaUj) * 100, 100);
  const barUj = document.getElementById("gauge-uber-je-bar");
  barUj.style.width = pctUj + "%";
  barUj.className = "gauge-bar " + (pctUj > 90 ? "red" : pctUj > 75 ? "yellow" : "");
  document.getElementById("sem-uj-spent").textContent = formatMoeda(spentUj);
  document.getElementById("sem-uj-avail").textContent = formatMoeda(availUj) + " livres";

  // 6. Compras Online & Jogos (Teto R$ 700/mês)
  const metaCo = tetos.teto_compras_online_mensal || 700;
  const spentCo = (sem.compras_online_mes || 0) + quickTotals.compras_online;
  const availCo = Math.max(metaCo - spentCo, 0);
  const pctCo = Math.min((spentCo / metaCo) * 100, 100);
  const barCo = document.getElementById("gauge-co-bar");
  barCo.style.width = pctCo + "%";
  barCo.className = "gauge-bar " + (pctCo > 90 ? "red" : pctCo > 75 ? "yellow" : "");
  document.getElementById("sem-co-spent").textContent = formatMoeda(spentCo) + " gastos";
  const elCoAvail = document.getElementById("sem-co-avail");
  elCoAvail.textContent = formatMoeda(availCo) + " livres";
  elCoAvail.className = "sem-avail " + (availCo <= 0 ? "danger" : "");

  setupQuickExpenseHandlers();
  setupCalculadoraJe();
}

function setupQuickExpenseHandlers() {
  const btnAdd = document.getElementById("btn-quick-add");
  const inCat = document.getElementById("quick-category");
  const inVal = document.getElementById("quick-val");
  const inDesc = document.getElementById("quick-desc");
  const listCont = document.getElementById("quick-entries-list");

  function renderList() {
    const list = getQuickExpenses();
    listCont.innerHTML = "";
    if (list.length === 0) {
      listCont.innerHTML = `<span class="text-sm text-muted">Nenhum gasto anotado nesta semana ainda.</span>`;
      return;
    }
    list.slice().reverse().forEach((item, revIdx) => {
      const realIdx = list.length - 1 - revIdx;
      const row = document.createElement("div");
      row.className = "quick-entry-row";
      const catLabels = {
        va: "🛒 VA",
        comer_fora: "🍕 Comer Fora",
        uber_guto: "🚗 Uber Guto",
        uber_je: "🚗 Uber Jé",
        compras_online: "📦 Online",
        outro: "💳 Geral",
      };
      row.innerHTML = `
        <div class="quick-entry-info">
          <span class="quick-entry-tag">${catLabels[item.cat] || item.cat}</span>
          <strong>${item.desc || "Sem descrição"}</strong>
          <span class="text-muted">(${item.data})</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <strong>${formatMoeda(item.val)}</strong>
          <button class="btn-del-entry" data-idx="${realIdx}" title="Apagar">✕</button>
        </div>
      `;
      listCont.appendChild(row);
    });

    listCont.querySelectorAll(".btn-del-entry").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.currentTarget.dataset.idx);
        const list = getQuickExpenses();
        list.splice(idx, 1);
        saveQuickExpenses(list);
        renderizarTelaAgora();
      });
    });
  }

  // Evento de adição
  btnAdd.onclick = () => {
    const val = parseFloat(inVal.value);
    if (!val || val <= 0) {
      alert("Por favor, digite um valor válido.");
      return;
    }
    const cat = inCat.value;
    const desc = inDesc.value.trim() || inCat.options[inCat.selectedIndex].text;
    const now = new Date();
    const dataStr = now.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

    const list = getQuickExpenses();
    list.push({ cat, val, desc, data: dataStr, ts: Date.now() });
    saveQuickExpenses(list);

    inVal.value = "";
    inDesc.value = "";
    renderizarTelaAgora();
  };

  renderList();
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

  btnEl.onclick = calcular;
  inputEl.oninput = calcular;
}

// ==============================================================================
// TELA 2: JÉ & CASA
// ==============================================================================

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

// ==============================================================================
// TELA 3: PARCELAS & CORTES
// ==============================================================================

function renderizarTelaParcelas() {
  const futs = appData.parcelas_futuras || [];
  const chartCont = document.getElementById("parcelas-chart-container");
  chartCont.innerHTML = "";

  const maxVal = Math.max(...futs.map((f) => f.total_parcelas), 1764.16);

  futs.forEach((f) => {
    const col = document.createElement("div");
    col.className = "chart-bar-col";
    const heightPct = Math.max((f.total_parcelas / maxVal) * 100, 6);
    const isLow = f.total_parcelas < 500;
    col.innerHTML = `
      <div class="chart-bar ${isLow ? "low" : ""}" style="height: ${heightPct}%;" title="${f.mes}: ${formatMoeda(f.total_parcelas)}"></div>
      <span class="chart-label">${f.mes.slice(5)}</span>
    `;
    chartCont.appendChild(col);
  });

  // Lista de Compras Parceladas Ativas
  renderizarComprasParceladas();

  // Lista de Assinaturas Ativas da Casa (Kotas R$ 8,70, Aquarius ativo, sem alertas antigos)
  renderizarAssinaturasAtivas();

  // Lembretes Operacionais LocalStorage
  setupChecklistCortes();
}

function renderizarAssinaturasAtivas() {
  const cont = document.getElementById("assinaturas-ativas-container");
  if (!cont) return;
  const subs = (appData.assinaturas || []).slice().sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  cont.innerHTML = `
    <div class="compras-parc-list">
      ${subs
        .map((s) => `
          <div class="compra-parc-row">
            <div class="compra-parc-info">
              <span class="compra-parc-desc">${s.nome}</span>
              <span class="compra-parc-meta">${s.status_recomendacao} • ${s.meses_ativos_count} meses ativos (Acumulado: ${formatMoeda(s.total_2026)})</span>
            </div>
            <span class="compra-parc-val" style="color: var(--primary);">${formatMoeda(s.ultimo_valor)}/mês</span>
          </div>
        `)
        .join("")}
    </div>
  `;
}

function renderizarComprasParceladas() {
  const cont = document.getElementById("parcelas-compras-container");
  if (!cont) return;

  // Filtra transações ativas de parcelamento de Novembro
  const txs = appData.todas_transacoes || [];
  const novParcelas = txs.filter((t) => t.ym === "2026-11" && t.inst_cur && t.inst_tot > 1);

  // Ordena por maior parcela mensal
  novParcelas.sort((a, b) => b.amount - a.amount);

  cont.innerHTML = `
    <div class="compras-parc-list">
      ${novParcelas
        .map((t) => {
          const restam = t.inst_tot - t.inst_cur;
          return `
            <div class="compra-parc-row">
              <div class="compra-parc-info">
                <span class="compra-parc-desc">${t.desc}</span>
                <span class="compra-parc-meta">${t.holder} (${t.source}) • Parcela ${t.inst_cur}/${t.inst_tot} • Restam ${restam}x</span>
              </div>
              <span class="compra-parc-val">${formatMoeda(t.amount)}/mês</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function setupChecklistCortes() {
  const chks = document.querySelectorAll(".chk-cut");

  chks.forEach((chk) => {
    const savedState = localStorage.getItem("chk_" + chk.id);
    if (savedState === "true") {
      chk.checked = true;
    }
    chk.onchange = () => {
      localStorage.setItem("chk_" + chk.id, chk.checked);
    };
  });
}

// ==============================================================================
// TELA 4: 8 SEÇÕES CANÔNICAS (ORDEM ALFABÉTICA), FILTROS E DRILL-DOWN UNIVERSAL
// ==============================================================================

function renderizarListaTransacoesMobileHTML(txs) {
  return `
    <div class="tx-list-mobile">
      ${txs
        .slice()
        .reverse()
        .map((t) => {
          const badgeClass =
            t.tipo === "VA"
              ? "badge-va"
              : t.holder === "AUGUSTO"
              ? "badge-guto"
              : "badge-je";
          const parcStr = t.inst_cur ? `${t.inst_cur}/${t.inst_tot}` : "";
          return `
            <div class="tx-row-item">
              <div class="tx-row-left">
                <span class="tx-row-desc">${t.desc}</span>
                <div class="tx-row-meta">
                  <span>${t.date || t.ym}</span>
                  <span class="badge-tag ${badgeClass}">${t.holder} (${t.source})</span>
                  ${parcStr ? `<span class="badge-tag badge-parc">${parcStr}</span>` : ""}
                </div>
              </div>
              <span class="tx-row-right">${formatMoeda(t.amount)}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function abrirModalDrillDown(categoriaNome, mesFiltro) {
  const modal = document.getElementById("drilldown-modal");
  const titleEl = document.getElementById("drilldown-title");
  const subEl = document.getElementById("drilldown-subtitle");
  const bodyEl = document.getElementById("drilldown-body");

  const allTxs = appData.todas_transacoes || [];
  const txs = allTxs.filter((t) => {
    if (t.category !== categoriaNome) return false;
    if (mesFiltro && mesFiltro !== "TODOS" && t.ym !== mesFiltro) return false;
    return true;
  });

  const tot = txs.reduce((s, t) => s + t.amount, 0);
  titleEl.textContent = categoriaNome;
  subEl.textContent = `${mesFiltro && mesFiltro !== "TODOS" ? "Mês " + mesFiltro : "Ano Inteiro (Jan-Nov/2026)"} • ${txs.length} lançamentos • Total: ${formatMoeda(tot)}`;

  bodyEl.innerHTML = txs.length > 0
    ? renderizarListaTransacoesMobileHTML(txs)
    : `<p class="text-muted text-sm">Nenhum lançamento encontrado.</p>`;

  modal.classList.remove("hidden");
}

function renderizarTelaRaioX() {
  const btnRanking = document.getElementById("btn-view-ranking");
  const btnMatriz = document.getElementById("btn-view-matriz");
  const viewRanking = document.getElementById("view-ranking-container");
  const viewMatriz = document.getElementById("view-matriz-container");

  // Modal close handlers
  const modal = document.getElementById("drilldown-modal");
  const btnCloseModal = document.getElementById("btn-close-drilldown");
  if (btnCloseModal && modal) {
    btnCloseModal.onclick = () => modal.classList.add("hidden");
    modal.onclick = (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    };
  }

  btnRanking.onclick = () => {
    btnRanking.classList.add("active");
    btnMatriz.classList.remove("active");
    viewRanking.classList.remove("hidden");
    viewMatriz.classList.add("hidden");
    currentViewMode = "ranking";
  };

  btnMatriz.onclick = () => {
    btnMatriz.classList.add("active");
    btnRanking.classList.remove("active");
    viewMatriz.classList.remove("hidden");
    viewRanking.classList.add("hidden");
    currentViewMode = "matriz";
    renderizarMatrizPanoramica();
  };

  const selMonth = document.getElementById("filter-month");
  const selHolder = document.getElementById("filter-holder");
  const selSource = document.getElementById("filter-source");
  const inSearch = document.getElementById("filter-search");

  function atualizarFiltros() {
    renderizarRankingComDrillDown();
    if (currentViewMode === "matriz") {
      renderizarMatrizPanoramica();
    }
  }

  selMonth.onchange = atualizarFiltros;
  selHolder.onchange = atualizarFiltros;
  selSource.onchange = atualizarFiltros;
  inSearch.oninput = atualizarFiltros;

  renderizarRankingComDrillDown();
  renderizarMatrizPanoramica();
}

function renderizarRankingComDrillDown() {
  const selMonth = document.getElementById("filter-month").value;
  const selHolder = document.getElementById("filter-holder").value;
  const selSource = document.getElementById("filter-source").value;
  const searchTerm = (document.getElementById("filter-search").value || "").toLowerCase().trim();

  const allTxs = appData.todas_transacoes || [];

  // 1. Filtragem das transações
  const filteredTxs = allTxs.filter((t) => {
    if (selMonth !== "TODOS" && t.ym !== selMonth) return false;
    if (selHolder !== "TODOS" && t.holder !== selHolder) return false;
    if (selSource !== "TODOS") {
      if (selSource === "CARTAO" && t.tipo !== "CARTAO") return false;
      if (selSource === "CONTA_CORRENTE" && t.tipo !== "CONTA") return false;
      if (selSource === "VALE_ALIMENTACAO" && t.tipo !== "VA") return false;
      if (selSource === "FOLHA" && t.tipo !== "FOLHA") return false;
    }
    if (searchTerm) {
      const matchDesc = (t.desc || "").toLowerCase().includes(searchTerm);
      const matchCat = (t.category || "").toLowerCase().includes(searchTerm);
      const matchSec = (t.section || "").toLowerCase().includes(searchTerm);
      const matchHolder = (t.holder || "").toLowerCase().includes(searchTerm);
      const matchVal = t.amount.toString().includes(searchTerm);
      if (!matchDesc && !matchCat && !matchSec && !matchHolder && !matchVal) return false;
    }
    return true;
  });

  // Atualiza barra de estatísticas
  const totalFiltrado = filteredTxs.reduce((sum, t) => sum + t.amount, 0);
  document.getElementById("stats-total").textContent = formatMoeda(totalFiltrado);
  document.getElementById("stats-count").textContent = filteredTxs.length.toLocaleString("pt-BR");

  // 2. Agrupa por Seção Canônica -> Categoria (em ordem alfabética)
  const secoesOrdem = (appData.metadata && appData.metadata.secoes_canonicas) || [
    "FAMÍLIA", "CLARA", "JÉ", "GUTO", "PETS", "CASA", "PARCELAMENTO CARTÃO & ASSINATURAS", "DESCONTOS EM FOLHA"
  ];

  const secGroups = {};
  filteredTxs.forEach((t) => {
    const sec = t.section || "FAMÍLIA";
    const cat = t.category || "Outros";
    if (!secGroups[sec]) secGroups[sec] = { total: 0, cats: {} };
    if (!secGroups[sec].cats[cat]) {
      secGroups[sec].cats[cat] = { total: 0, totalGuto: 0, totalJe: 0, txs: [] };
    }
    secGroups[sec].total += t.amount;
    secGroups[sec].cats[cat].total += t.amount;
    if (t.holder === "AUGUSTO") secGroups[sec].cats[cat].totalGuto += t.amount;
    else if (t.holder === "JESSICA") secGroups[sec].cats[cat].totalJe += t.amount;
    secGroups[sec].cats[cat].txs.push(t);
  });

  const container = document.getElementById("view-ranking-container");
  container.innerHTML = "";

  const activeSecs = secoesOrdem.filter((s) => secGroups[s]);
  if (activeSecs.length === 0) {
    container.innerHTML = `
      <div class="card text-center py-4">
        <p class="text-muted">Nenhum lançamento encontrado para os filtros selecionados.</p>
      </div>
    `;
    return;
  }

  activeSecs.forEach((secName, secIdx) => {
    const secData = secGroups[secName];

    // Cabeçalho da Seção
    const secHeader = document.createElement("div");
    secHeader.className = "sec-group-header";
    secHeader.innerHTML = `
      <span>${secIdx + 1}. ${secName}</span>
      <span class="sec-group-total">${formatMoeda(secData.total)}</span>
    `;
    container.appendChild(secHeader);

    // Categorias em ordem alfabética (A-Z) dentro da seção
    const sortedCats = Object.keys(secData.cats).sort((a, b) => a.localeCompare(b, "pt-BR"));
    sortedCats.forEach((catName) => {
      const grp = secData.cats[catName];
      const pct = totalFiltrado > 0 ? (grp.total / totalFiltrado) * 100 : 0;

      const acc = document.createElement("div");
      acc.className = "cat-accordion";

      acc.innerHTML = `
        <div class="cat-acc-head">
          <div class="cat-acc-left">
            <div class="cat-name-block">
              <span class="cat-name-title">${catName}</span>
              <span class="cat-sub-info">
                ${grp.txs.length} ${grp.txs.length === 1 ? "lançamento" : "lançamentos"} • 
                Guto: ${formatMoeda(grp.totalGuto)} | Jé: ${formatMoeda(grp.totalJe)}
              </span>
            </div>
          </div>
          <div class="cat-acc-right">
            <div class="cat-total-block">
              <span class="cat-total-val">${formatMoeda(grp.total)}</span>
              <span class="cat-pct-label">${pct.toFixed(1)}%</span>
            </div>
            <span class="cat-arrow">▼</span>
          </div>
        </div>
        <div class="cat-bar-mini-wrap">
          <div class="cat-bar-mini" style="width: ${Math.min(pct, 100)}%;"></div>
        </div>
        <div class="cat-acc-body">
          ${renderizarListaTransacoesMobileHTML(grp.txs)}
        </div>
      `;

      const head = acc.querySelector(".cat-acc-head");
      head.addEventListener("click", () => {
        acc.classList.toggle("open");
      });

      container.appendChild(acc);
    });
  });
}

function renderizarMatrizPanoramica() {
  const container = document.getElementById("view-matriz-container");
  const secoesResumo = appData.secoes_resumo || [];
  if (secoesResumo.length === 0) return;

  const meses = [
    "2026-11", "2026-10", "2026-09", "2026-08", "2026-07",
    "2026-06", "2026-05", "2026-04", "2026-03", "2026-02", "2026-01"
  ];
  const mesesHeaders = [
    "Nov", "Out", "Set", "Ago", "Jul", "Jun", "Mai", "Abr", "Mar", "Fev", "Jan"
  ];

  // Colunas Total 2026 e Média/Mês logo após a Categoria para leitura imediata no celular!
  let html = `
    <table class="matriz-table">
      <thead>
        <tr>
          <th>Categoria</th>
          <th style="background: rgba(56, 189, 248, 0.1);">Total 2026</th>
          <th style="background: rgba(16, 185, 129, 0.1);">Média/Mês</th>
          ${mesesHeaders.map((m) => `<th>${m}</th>`).join("")}
        </tr>
      </thead>
      <tbody>
  `;

  secoesResumo.forEach((sec) => {
    html += `
      <tr class="matriz-sec-row">
        <td colspan="${3 + meses.length}">${sec.secao}</td>
      </tr>
    `;

    const cats = (sec.categorias || []).slice().sort((a, b) => a.categoria.localeCompare(b.categoria, "pt-BR"));
    cats.forEach((c) => {
      const safeCat = c.categoria.replace(/"/g, "&quot;");
      html += `
        <tr>
          <td class="matriz-cell-clickable" data-cat="${safeCat}" data-ym="TODOS">${c.categoria}</td>
          <td class="col-total matriz-cell-clickable" data-cat="${safeCat}" data-ym="TODOS">${formatMoeda(c.total_ano)}</td>
          <td class="col-media">${formatMoeda(c.media_mes)}</td>
          ${meses
            .map((ym) => {
              const v = c.por_mes[ym] || 0;
              if (v > 0) {
                return `<td class="matriz-cell-clickable" data-cat="${safeCat}" data-ym="${ym}">${formatMoeda(v)}</td>`;
              }
              return `<td>-</td>`;
            })
            .join("")}
        </tr>
      `;
    });

    html += `
      <tr class="matriz-sub-row">
        <td>Subtotal ${sec.secao}</td>
        <td class="col-total">${formatMoeda(sec.total_ano)}</td>
        <td class="col-media">${formatMoeda(sec.media_mes)}</td>
        ${meses
          .map((ym) => {
            const sv = (sec.subtotal_por_mes && sec.subtotal_por_mes[ym]) || 0;
            return `<td>${sv > 0 ? formatMoeda(sv) : "-"}</td>`;
          })
          .join("")}
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  container.innerHTML = html;

  // Bind click drill-down em todas as células clicáveis da Matriz Panorâmica
  container.querySelectorAll(".matriz-cell-clickable").forEach((cell) => {
    cell.addEventListener("click", () => {
      const cat = cell.dataset.cat;
      const ym = cell.dataset.ym;
      abrirModalDrillDown(cat, ym);
    });
  });
}

// ==============================================================================
// 5. NAVEGAÇÃO ENTRE ABAS E TEMA
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
// 6. INICIALIZAÇÃO AUTOMÁTICA
// ==============================================================================

window.addEventListener("DOMContentLoaded", async () => {
  setupKeypad();
  setupNavigation();

  if ("serviceWorker" in navigator) {
    try {
      await navigator.serviceWorker.register("sw.js");
      console.log("Service Worker PWA registrado!");
    } catch (e) {
      console.log("Service Worker erro:", e);
    }
  }

  const savedPin = sessionStorage.getItem("casa_pin");
  if (savedPin) {
    tentarDesbloqueio(savedPin);
  }
});
