const state = {
  n: 3,
  order: 6,
  page: 1,
  pageSize: 25,
  pages: 1,
  query: "",
  filter: "all",
  overviewPage: 1,
  overviewPages: 1,
  overviewQuery: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function setStatus(text, mode = "") {
  const el = $("#status");
  el.textContent = text;
  el.className = `status ${mode}`.trim();
}

async function api(path, options = {}) {
  setStatus("computing", "busy");
  try {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    setStatus("ready");
    return payload;
  } catch (error) {
    setStatus("error", "error");
    throw error;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function factorial(n) {
  let x = 1;
  for (let i = 2; i <= n; i += 1) x *= i;
  return x;
}

function subscriptNumber(n) {
  const map = {0:"₀",1:"₁",2:"₂",3:"₃",4:"₄",5:"₅",6:"₆",7:"₇",8:"₈",9:"₉"};
  return String(n).split("").map(d => map[d]).join("");
}

function showView(name) {
  $$(".nav-item").forEach(btn => btn.classList.toggle("active", btn.dataset.view === name));
  $$(".view").forEach(view => view.classList.toggle("active", view.id === `view-${name}`));
  const titles = {
    overview: `S${subscriptNumber(state.n)} Explorer`,
    elements: "Elements",
    compose: "Composition",
    cayley: "Cayley Table",
    dihedral: "Dihedral Explorer",
    subgroups: "Subgroups & Quotients",
    conjugacy: "Conjugacy Classes"
  };
  const subtitles = {
    overview: "Explore the structure, elements, and subgroups of the symmetric group",
    elements: `Browse and inspect every permutation in S${subscriptNumber(state.n)}`,
    compose: "Compose permutations using the convention σ ∘ τ",
    cayley: "Explore the complete multiplication structure for small symmetric groups",
    dihedral: "Construct the symmetries of a regular polygon as permutations",
    subgroups: "Generate subgroups, test normality, and construct quotient groups",
    conjugacy: "Classify permutations by cycle type"
  };
  $("#page-title").innerHTML = name === "overview"
    ? `<span class="math-italic">S</span><sub>${state.n}</sub> Explorer`
    : titles[name];
  $("#page-subtitle").textContent = subtitles[name];
}

function insightFor(n) {
  if (n === 1) return "S₁ is the trivial group: the smallest possible permutation group, containing only the identity.";
  if (n === 2) return "S₂ is cyclic of order 2. It is the first nontrivial symmetric group and is abelian.";
  if (n === 3) return "S₃ is the smallest non-abelian group. It is isomorphic to the dihedral group D₃, the symmetries of an equilateral triangle.";
  if (n === 4) return "S₄ is the full symmetry group of four labeled objects and contains the normal Klein four subgroup V₄.";
  return `S${subscriptNumber(n)} has ${factorial(n).toLocaleString()} elements. For n ≥ 5, its alternating subgroup A${subscriptNumber(n)} is simple.`;
}

function renderAbout() {
  const even = Number($("#count-even").textContent.replaceAll(",", "")) || 0;
  const odd = Number($("#count-odd").textContent.replaceAll(",", "")) || 0;
  const classes = $("#count-classes").textContent;
  const baseSet = state.n <= 5 ? `{${Array.from({length: state.n}, (_, i) => i + 1).join(", ")}}` : `{1, 2, …, ${state.n}}`;
  $("#hero-description").textContent = `The symmetric group S${subscriptNumber(state.n)} is the group of all permutations of ${baseSet}.`;
  $("#about-list").innerHTML = `
    <li>Order: |S${subscriptNumber(state.n)}| = ${state.n}! = ${state.order.toLocaleString()}</li>
    <li>Even elements: ${even.toLocaleString()}${state.order ? ` (${Math.round(even/state.order*100)}%)` : ""}</li>
    <li>Odd elements: ${odd.toLocaleString()}${state.order ? ` (${Math.round(odd/state.order*100)}%)` : ""}</li>
    <li>Conjugacy classes: ${classes}</li>
    <li>Conjugacy classes correspond exactly to cycle types (partitions of n).</li>`;
  $("#key-insight").textContent = insightFor(state.n);
}

async function loadGroup() {
  state.order = factorial(state.n);
  $("#n-input").value = state.n;
  $("#side-order").textContent = state.order.toLocaleString();
  $("#hero-order").textContent = state.order.toLocaleString();
  $("#formula-n").textContent = state.n;
  $("#formula-factorial").textContent = `${state.n}!`;
  $$(".dynamic-n").forEach(el => el.textContent = state.n);
  $("#sigma-index").max = state.order;
  $("#tau-index").max = state.order;
  $("#overview-index").max = state.order;
  state.page = 1;
  state.overviewPage = 1;
  await loadElements();
  const classes = await api(`/api/conjugacy?n=${state.n}`);
  $("#count-classes").textContent = classes.class_count;
  await loadOverviewElements();
  await inspectOverviewPermutation(1);
  renderAbout();
  const active = $(".nav-item.active")?.dataset.view || "overview";
  showView(active);
}

async function loadOverviewElements() {
  const params = new URLSearchParams({
    n: state.n,
    page: state.overviewPage,
    page_size: 10,
    query: state.overviewQuery,
    filter: "all",
  });
  try {
    const data = await api(`/api/group?${params}`);
    state.overviewPage = data.pagination.page;
    state.overviewPages = data.pagination.pages;
    const tbody = $("#overview-elements-body");
    tbody.innerHTML = data.elements.map(row => `
      <tr data-index="${row.index}">
        <td>${row.index}</td>
        <td class="code-line">${escapeHtml(row.one_line)}</td>
        <td class="code-line">${escapeHtml(row.cycles)}</td>
        <td>${row.order}</td>
        <td class="${row.sign === 1 ? "sign-even" : "sign-odd"}">${row.sign === 1 ? "+" : "−"}</td>
      </tr>`).join("");
    $("#overview-page-label").textContent = `${state.overviewPage}`;
    tbody.querySelectorAll("tr").forEach(tr => tr.addEventListener("click", () => inspectOverviewPermutation(Number(tr.dataset.index))));
  } catch (error) {
    $("#overview-elements-body").innerHTML = `<tr><td colspan="5">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderCycleVisualization(p) {
  const svg = $("#cycle-svg");
  const values = p.permutation;
  const n = values.length;
  const cx = 180, cy = 150;
  const radius = n <= 3 ? 92 : n <= 5 ? 105 : 112;
  const nodeR = n >= 7 ? 17 : 22;
  const pts = values.map((_, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i / n);
    return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
  });
  let edges = "";
  for (let i = 0; i < n; i += 1) {
    const j = values[i];
    const [x1,y1] = pts[i];
    const [x2,y2] = pts[j];
    if (i === j) {
      const loopR = nodeR + 12;
      edges += `<path class="cycle-loop" d="M ${x1-nodeR*.45} ${y1-nodeR*.85} C ${x1-loopR*1.45} ${y1-loopR*2.2}, ${x1+loopR*1.45} ${y1-loopR*2.2}, ${x1+nodeR*.55} ${y1-nodeR*.78}" />`;
    } else {
      const dx=x2-x1, dy=y2-y1, len=Math.hypot(dx,dy) || 1;
      const sx=x1+dx/len*(nodeR+3), sy=y1+dy/len*(nodeR+3);
      const ex=x2-dx/len*(nodeR+8), ey=y2-dy/len*(nodeR+8);
      const bend = n <= 3 ? 17 : 10;
      const mx=(sx+ex)/2 - dy/len*bend, my=(sy+ey)/2 + dx/len*bend;
      edges += `<path class="cycle-edge" d="M ${sx} ${sy} Q ${mx} ${my} ${ex} ${ey}" />`;
    }
  }
  const nodes = pts.map(([x,y],i) => `<circle class="cycle-node" cx="${x}" cy="${y}" r="${nodeR}"/><text class="cycle-node-label" x="${x}" y="${y+1}">${i+1}</text>`).join("");
  svg.innerHTML = `<defs><marker id="arrowhead" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L8,3 z" fill="#80b5ff"/></marker></defs>${edges}${nodes}`;
  $("#cycle-caption").textContent = p.identity ? "This is the identity permutation." : `Cycle form: ${p.cycles}. Each arrow shows i ↦ σ(i).`;
}

async function inspectOverviewPermutation(index) {
  try {
    const p = await api(`/api/permutation?n=${state.n}&index=${index}`);
    $("#overview-index").value = index;
    $$("#overview-elements-body tr").forEach(tr => tr.classList.toggle("selected", Number(tr.dataset.index) === index));
    $("#overview-inspector").innerHTML = `
      <table class="detail-table"><tbody>
        <tr><td>One-line notation:</td><td>${escapeHtml(p.one_line)}</td></tr>
        <tr><td>Cycle notation:</td><td>${escapeHtml(p.cycles)}</td></tr>
        <tr><td>Cycle type:</td><td>[${escapeHtml(p.cycle_type.join(", "))}]</td></tr>
        <tr><td>Order:</td><td>${p.order}</td></tr>
        <tr><td>Sign / Parity:</td><td class="${p.sign === 1 ? "sign-even" : ""}">${p.sign === 1 ? "+1 (even)" : "−1 (odd)"}</td></tr>
        <tr><td>Inverse:</td><td>${escapeHtml(p.inverse_one_line)}</td></tr>
        <tr><td>Is identity:</td><td class="${p.identity ? "sign-even" : ""}">${p.identity ? "Yes" : "No"}</td></tr>
        <tr><td>Is self-inverse:</td><td class="${p.self_inverse ? "sign-even" : ""}">${p.self_inverse ? "Yes" : "No"}</td></tr>
      </tbody></table>`;
    renderCycleVisualization(p);
  } catch (error) {
    $("#overview-inspector").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function loadElements() {
  const params = new URLSearchParams({
    n: state.n,
    page: state.page,
    page_size: state.pageSize,
    query: state.query,
    filter: state.filter,
  });
  try {
    const data = await api(`/api/group?${params}`);
    state.page = data.pagination.page;
    state.pages = data.pagination.pages;
    state.order = data.order;
    $("#count-even").textContent = data.counts.even.toLocaleString();
    $("#count-odd").textContent = data.counts.odd.toLocaleString();
    $("#count-involutions").textContent = data.counts.self_inverse.toLocaleString();
    $("#page-label").textContent = `page ${state.page} of ${state.pages} · ${data.pagination.total_filtered.toLocaleString()} matching`;

    const tbody = $("#elements-table tbody");
    tbody.innerHTML = data.elements.map(row => `
      <tr data-index="${row.index}">
        <td>${row.index}</td>
        <td class="code-line">${escapeHtml(row.one_line)}</td>
        <td class="code-line">${escapeHtml(row.cycles)}</td>
        <td>${row.order}</td>
        <td><span class="badge ${row.parity}">${row.parity}</span></td>
        <td>${row.self_inverse ? "yes" : ""}</td>
      </tr>`).join("");
    tbody.querySelectorAll("tr").forEach(tr => tr.addEventListener("click", () => inspectPermutation(Number(tr.dataset.index))));
  } catch (error) {
    $("#elements-table tbody").innerHTML = `<tr><td colspan="6">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function inspectPermutation(index) {
  try {
    const p = await api(`/api/permutation?n=${state.n}&index=${index}`);
    $("#inspector").innerHTML = `
      <p class="eyebrow">ELEMENT #${p.index}</p>
      <h3 class="code-line">${escapeHtml(p.cycles)}</h3>
      <p class="code-line muted">${escapeHtml(p.one_line)}</p>
      <div class="fact-grid">
        <div class="fact"><span>order</span><strong>${p.order}</strong></div>
        <div class="fact"><span>parity</span><strong>${p.parity}</strong></div>
        <div class="fact"><span>cycle type</span><strong>${escapeHtml(p.cycle_type.join(" + "))}</strong></div>
        <div class="fact"><span>self-inverse</span><strong>${p.self_inverse ? "yes" : "no"}</strong></div>
      </div>
      <p class="metric-label">inverse</p>
      <p class="code-line">${escapeHtml(p.inverse_cycles)}</p>
      <p class="code-line muted">${escapeHtml(p.inverse_one_line)}</p>`;
  } catch (error) {
    $("#inspector").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function composeSelected() {
  const sigma = Number($("#sigma-index").value);
  const tau = Number($("#tau-index").value);
  try {
    const data = await api("/api/compose", {
      method: "POST",
      body: JSON.stringify({ n: state.n, sigma, tau }),
    });
    const card = (symbol, p, result = false) => `
      <article class="card perm-card ${result ? "result" : ""}">
        <div class="symbol">${symbol} · element #${p.index}</div>
        <div class="cycles code-line">${escapeHtml(p.cycles)}</div>
        <div class="code-line muted">${escapeHtml(p.one_line)}</div>
        <div class="fact-grid"><div class="fact"><span>order</span><strong>${p.order}</strong></div><div class="fact"><span>parity</span><strong>${p.parity}</strong></div></div>
      </article>`;
    $("#compose-result").innerHTML = card("σ", data.sigma) + card("τ", data.tau) + card("σ ∘ τ", data.result, true);
  } catch (error) {
    $("#compose-result").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function loadCayley() {
  const output = $("#cayley-output");
  if (state.n > 4) {
    output.innerHTML = `<div class="notice">S${subscriptNumber(state.n)} has ${state.order.toLocaleString()} elements. A full Cayley table would contain ${(state.order * state.order).toLocaleString()} cells. This explorer caps the view at n ≤ 4.</div>`;
    return;
  }
  try {
    const data = await api(`/api/cayley?n=${state.n}`);
    const header = `<tr><th>∘</th>${data.labels.map((label, i) => `<th title="${escapeHtml(data.one_line[i])}">${i + 1}</th>`).join("")}</tr>`;
    const rows = data.table.map((row, i) => `<tr><th title="${escapeHtml(data.labels[i])}">${i + 1}</th>${row.map(value => `<td>${value}</td>`).join("")}</tr>`).join("");
    output.innerHTML = `<div class="cayley-shell"><table class="cayley"><thead>${header}</thead><tbody>${rows}</tbody></table></div><p class="note">Hover a row/column index to see the corresponding permutation in the browser tooltip.</p>`;
  } catch (error) {
    output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

function renderPolygon(m) {
  const svg = $("#polygon-svg");
  const cx = 250, cy = 250, r = 185;
  const points = [];
  for (let i = 0; i < m; i += 1) {
    const theta = -Math.PI / 2 + 2 * Math.PI * i / m;
    points.push([cx + r * Math.cos(theta), cy + r * Math.sin(theta)]);
  }
  const polyPoints = points.map(([x,y]) => `${x},${y}`).join(" ");
  svg.innerHTML = `<polygon class="polygon-edge" points="${polyPoints}" /><circle class="center-mark" cx="${cx}" cy="${cy}" r="4" />` +
    points.map(([x,y], i) => `<circle class="vertex" cx="${x}" cy="${y}" r="17"/><text class="vertex-label" x="${x}" y="${y}">${i}</text>`).join("");
}

async function loadDihedral() {
  const m = Number($("#dihedral-m").value);
  try {
    const data = await api(`/api/dihedral?m=${m}`);
    renderPolygon(m);
    $("#dihedral-relations").innerHTML = data.relations.map(r => `<code>${escapeHtml(r)}</code>`).join("");
    $("#dihedral-summary").innerHTML = `<strong>D${subscriptNumber(m)}</strong> has ${data.order} elements: ${m} rotations and ${m} reflections.`;
    $("#dihedral-table tbody").innerHTML = data.elements.map(e => `<tr><td class="code-line">${escapeHtml(e.name)}</td><td>${e.type}</td><td class="code-line">${escapeHtml(e.cycles)}</td><td>${e.order}</td></tr>`).join("");
  } catch (error) {
    $("#dihedral-summary").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function generateSubgroup() {
  const output = $("#generated-subgroup-output");
  const generators = $("#generator-indices").value.split(",").map(x => Number(x.trim())).filter(Number.isFinite);
  try {
    const data = await api("/api/generated-subgroup", { method: "POST", body: JSON.stringify({ n: state.n, generators }) });
    output.innerHTML = `<div class="fact-grid"><div class="fact"><span>order</span><strong>${data.order}</strong></div><div class="fact"><span>normal in Sₙ</span><strong>${data.normal_in_sn ? "yes" : "no"}</strong></div></div><div class="member-list">${data.members.map(x => escapeHtml(x.cycles)).join(" · ")}</div>`;
  } catch (error) {
    output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSubgroups() {
  const output = $("#subgroups-output");
  $("#quotient-output").innerHTML = "";
  if (state.n > 4) {
    output.innerHTML = `<div class="notice">Exhaustive subgroup enumeration is capped at n ≤ 4. Use “Generated subgroup” above for larger n.</div>`;
    return;
  }
  try {
    const data = await api(`/api/subgroups?n=${state.n}`);
    $("#subgroup-summary").innerHTML = `<div class="fact-grid"><div class="fact"><span>subgroups found</span><strong>${data.count}</strong></div><div class="fact"><span>|Sₙ|</span><strong>${data.group_order}</strong></div></div>`;
    output.innerHTML = data.subgroups.map(h => `
      <article class="card subgroup-card">
        <header><h4>H${h.index} · order ${h.order}</h4><span class="badge ${h.normal ? "normal" : "not-normal"}">${h.normal ? "normal" : "not normal"}</span></header>
        <div class="members">${h.members.map(m => escapeHtml(m.cycles)).join(" · ")}</div>
        ${h.normal ? `<button class="button quotient-button" data-index="${h.index}">Build Sₙ/H</button>` : ""}
      </article>`).join("");
    $$(".quotient-button").forEach(btn => btn.addEventListener("click", () => loadQuotient(Number(btn.dataset.index))));
  } catch (error) {
    output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function loadQuotient(subgroupIndex) {
  const output = $("#quotient-output");
  try {
    const data = await api(`/api/quotient?n=${state.n}&subgroup=${subgroupIndex}`);
    const q = data.quotient;
    const tableHeader = `<tr><th>·</th>${q.cosets.map(c => `<th>C${c.index}</th>`).join("")}</tr>`;
    const tableRows = q.table.map((row, i) => `<tr><th>C${i+1}</th>${row.map(v => `<td>${v}</td>`).join("")}</tr>`).join("");
    output.innerHTML = `<article class="card quotient-card"><h3>S${subscriptNumber(state.n)} / H${subgroupIndex}</h3><p class="muted">|H| = ${data.subgroup_order}; quotient order = ${q.order}; identity coset = C${q.identity_coset}.</p><div class="quotient-cosets">${q.cosets.map(c => `<div class="coset"><strong>C${c.index}${c.identity ? " · identity" : ""}</strong><div class="metric-label">order ${c.order}</div><div class="code-line">${escapeHtml(c.members.join(" · "))}</div></div>`).join("")}</div><div class="cayley-shell"><table class="cayley"><thead>${tableHeader}</thead><tbody>${tableRows}</tbody></table></div></article>`;
    output.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

async function loadConjugacy() {
  const output = $("#conjugacy-output");
  try {
    const data = await api(`/api/conjugacy?n=${state.n}`);
    $("#count-classes").textContent = data.class_count;
    output.innerHTML = `<div class="card table-card"><div class="table-wrap"><table><thead><tr><th>cycle type</th><th>class size</th><th>representative</th><th>order</th><th>parity</th></tr></thead><tbody>${data.classes.map(c => `<tr><td>${escapeHtml(c.cycle_type.join(" + "))}</td><td>${c.size}</td><td class="code-line">${escapeHtml(c.representative_cycles)}</td><td>${c.order}</td><td><span class="badge ${c.parity}">${c.parity}</span></td></tr>`).join("")}</tbody></table></div></div>`;
  } catch (error) {
    output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

function debounce(fn, ms = 250) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

$$(".nav-item").forEach(btn => btn.addEventListener("click", () => showView(btn.dataset.view)));
$("#apply-n").addEventListener("click", async () => {
  const n = Number($("#n-input").value);
  if (!Number.isInteger(n) || n < 1 || n > 8) { setStatus("n must be 1–8", "error"); return; }
  state.n = n;
  await loadGroup();
  $("#compose-result").innerHTML = "";
  $("#cayley-output").innerHTML = "";
  $("#subgroups-output").innerHTML = "";
  $("#quotient-output").innerHTML = "";
  $("#conjugacy-output").innerHTML = "";
});
$("#n-input").addEventListener("change", () => $("#apply-n").click());
$("#overview-load").addEventListener("click", () => inspectOverviewPermutation(Number($("#overview-index").value)));
$("#overview-index").addEventListener("keydown", e => { if (e.key === "Enter") inspectOverviewPermutation(Number(e.currentTarget.value)); });
$("#overview-search").addEventListener("input", debounce(async e => { state.overviewQuery = e.target.value; state.overviewPage = 1; await loadOverviewElements(); }));
$("#overview-prev").addEventListener("click", async () => { if (state.overviewPage > 1) { state.overviewPage -= 1; await loadOverviewElements(); } });
$("#overview-next").addEventListener("click", async () => { if (state.overviewPage < state.overviewPages) { state.overviewPage += 1; await loadOverviewElements(); } });
$("#element-search").addEventListener("input", debounce(async (e) => { state.query = e.target.value; state.page = 1; await loadElements(); }));
$("#element-filter").addEventListener("change", async (e) => { state.filter = e.target.value; state.page = 1; await loadElements(); });
$("#page-size").addEventListener("change", async (e) => { state.pageSize = Number(e.target.value); state.page = 1; await loadElements(); });
$("#prev-page").addEventListener("click", async () => { if (state.page > 1) { state.page -= 1; await loadElements(); } });
$("#next-page").addEventListener("click", async () => { if (state.page < state.pages) { state.page += 1; await loadElements(); } });
$("#compose-button").addEventListener("click", composeSelected);
$("#load-cayley").addEventListener("click", loadCayley);
$("#load-dihedral").addEventListener("click", loadDihedral);
$("#generate-subgroup").addEventListener("click", generateSubgroup);
$("#load-subgroups").addEventListener("click", loadSubgroups);
$("#load-conjugacy").addEventListener("click", loadConjugacy);

loadGroup().then(loadDihedral).catch(error => setStatus(error.message, "error"));
