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
  if (Number($("#sigma-index").value) > state.order) $("#sigma-index").value = 1;
  if (Number($("#tau-index").value) > state.order) $("#tau-index").value = 1;
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

const compositionAnimation = {
  data: null,
  index: 0,
  runId: 0,
  playing: false,
  autoplayTimer: null,
  requestId: 0,
};

function oneLineDigits(p) {
  return p.permutation.map(value => value + 1);
}

function cauchyMatrixHtml(p, label) {
  const top = Array.from({ length: p.permutation.length }, (_, i) => i + 1);
  const bottom = oneLineDigits(p);
  return `
    <div class="cauchy-block">
      <div class="cauchy-symbol">${label}</div>
      <div class="cauchy-paren">(</div>
      <div class="cauchy-grid" style="--n:${top.length}">
        ${top.map(v => `<span class="cauchy-top">${v}</span>`).join("")}
        ${bottom.map(v => `<span class="cauchy-bottom">${v}</span>`).join("")}
      </div>
      <div class="cauchy-paren">)</div>
    </div>`;
}

function cancelCompositionAnimation() {
  compositionAnimation.runId += 1;
  compositionAnimation.playing = false;
  clearTimeout(compositionAnimation.autoplayTimer);
  compositionAnimation.autoplayTimer = null;
  $$("#composition-trace-svg .composition-path.animating").forEach(path => path.classList.remove("animating"));
  const play = $("#composition-play-all");
  if (play) play.textContent = "Play all traces";
}

function compositionGeometry(n) {
  const width = 900;
  const top = 92;
  const step = n <= 4 ? 64 : n <= 6 ? 52 : 45;
  const height = Math.max(350, top + (n - 1) * step + 88);
  const xs = [120, 450, 780];
  const y = value => top + (value - 1) * step;
  return { width, height, xs, y };
}

function tracePathD(x1, y1, x2, y2) {
  const bend = Math.max(80, Math.abs(x2 - x1) * 0.34);
  return `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;
}

function renderCompositionDiagram(index = 0) {
  const data = compositionAnimation.data;
  const svg = $("#composition-trace-svg");
  if (!data || !svg) return;
  const n = data.n;
  const trace = data.trace[index];
  const { width, height, xs, y } = compositionGeometry(n);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const laneLabels = [
    ["Input", "i"],
    ["After τ", "τ(i)"],
    ["After σ", "σ(τ(i))"],
  ];
  const headers = laneLabels.map(([a,b], lane) => `
    <text class="composition-lane-title" x="${xs[lane]}" y="30">${a}</text>
    <text class="composition-lane-subtitle" x="${xs[lane]}" y="52">${b}</text>`).join("");

  const laneLines = xs.map(x => `<line class="composition-lane-line" x1="${x}" y1="68" x2="${x}" y2="${height - 36}"/>`).join("");
  const nodes = xs.map((x, lane) => Array.from({ length: n }, (_, k) => {
    const value = k + 1;
    const active = (lane === 0 && value === trace.input) ||
      (lane === 1 && value === trace.after_tau) ||
      (lane === 2 && value === trace.result);
    return `<g class="composition-node-group ${active ? "target" : ""}" data-lane="${lane}" data-value="${value}">
      <circle class="composition-node" cx="${x}" cy="${y(value)}" r="20"/>
      <text class="composition-node-label" x="${x}" y="${y(value) + 1}">${value}</text>
    </g>`;
  }).join("")).join("");

  const p1 = tracePathD(xs[0] + 22, y(trace.input), xs[1] - 22, y(trace.after_tau));
  const p2 = tracePathD(xs[1] + 22, y(trace.after_tau), xs[2] - 22, y(trace.result));
  svg.innerHTML = `
    <defs>
      <marker id="composition-arrow-blue" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#5ea0ff"/></marker>
      <marker id="composition-arrow-violet" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#a477ff"/></marker>
      <filter id="composition-glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    ${headers}${laneLines}
    <text class="composition-map-label tau" x="285" y="73">τ</text>
    <text class="composition-map-label sigma" x="615" y="73">σ</text>
    <path id="composition-path-tau" class="composition-path tau" d="${p1}"/>
    <path id="composition-path-sigma" class="composition-path sigma" d="${p2}"/>
    ${nodes}
    <circle id="composition-token" class="composition-token" cx="${xs[0]}" cy="${y(trace.input)}" r="10"/>
  `;
  updateCompositionReadout(index, 0);
}

function updateCompositionReadout(index, phase = 0) {
  const data = compositionAnimation.data;
  if (!data) return;
  compositionAnimation.index = index;
  const t = data.trace[index];
  const readout = $("#composition-current-trace");
  if (readout) {
    const first = phase >= 1 ? `<strong class="trace-tau">${t.input} → ${t.after_tau}</strong>` : `<strong>${t.input}</strong>`;
    const second = phase >= 2 ? `<strong class="trace-sigma"> → ${t.result}</strong>` : "";
    const explanation = phase === 0
      ? `Start with i = ${t.input}.`
      : phase === 1
      ? `First apply τ: τ(${t.input}) = ${t.after_tau}.`
      : `Then apply σ: σ(${t.after_tau}) = ${t.result}. Therefore (σ ∘ τ)(${t.input}) = ${t.result}.`;
    readout.innerHTML = `<div class="trace-expression">${first}${second}</div><div class="trace-explanation">${explanation}</div>`;
  }
  $$(".trace-chip").forEach((chip, i) => {
    chip.classList.toggle("active", i === index);
    chip.classList.toggle("complete", i < index || (i === index && phase >= 2));
  });
  const counter = $("#composition-trace-counter");
  if (counter) counter.textContent = `trace ${index + 1} of ${data.trace.length}`;
}

function setPathProgress(path, progress) {
  if (!path) return;
  const length = path.getTotalLength();
  path.style.strokeDasharray = `${length}`;
  path.style.strokeDashoffset = `${length * (1 - progress)}`;
}

function animateSvgPath(path, token, duration, runId) {
  return new Promise(resolve => {
    const length = path.getTotalLength();
    const start = performance.now();
    path.classList.add("animating");
    const frame = now => {
      if (runId !== compositionAnimation.runId) { resolve(false); return; }
      const raw = Math.min(1, (now - start) / duration);
      const eased = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
      setPathProgress(path, eased);
      const pt = path.getPointAtLength(length * eased);
      token.setAttribute("cx", pt.x);
      token.setAttribute("cy", pt.y);
      if (raw < 1) requestAnimationFrame(frame);
      else { path.classList.remove("animating"); resolve(true); }
    };
    requestAnimationFrame(frame);
  });
}

function animationDuration() {
  const speed = Number($("#composition-speed")?.value || 1);
  return 720 / speed;
}

async function animateCompositionTrace(index, runId = null) {
  if (!compositionAnimation.data) return false;
  if (runId === null) {
    cancelCompositionAnimation();
    runId = compositionAnimation.runId;
  }
  compositionAnimation.index = index;
  renderCompositionDiagram(index);
  const path1 = $("#composition-path-tau");
  const path2 = $("#composition-path-sigma");
  const token = $("#composition-token");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setPathProgress(path1, 1);
    setPathProgress(path2, 1);
    const end = path2.getPointAtLength(path2.getTotalLength());
    token.setAttribute("cx", end.x);
    token.setAttribute("cy", end.y);
    updateCompositionReadout(index, 2);
    return true;
  }
  setPathProgress(path1, 0);
  setPathProgress(path2, 0);

  updateCompositionReadout(index, 0);
  let ok = await animateSvgPath(path1, token, animationDuration(), runId);
  if (!ok) return false;
  updateCompositionReadout(index, 1);
  await new Promise(resolve => setTimeout(resolve, 180));
  if (runId !== compositionAnimation.runId) return false;

  ok = await animateSvgPath(path2, token, animationDuration(), runId);
  if (!ok) return false;
  updateCompositionReadout(index, 2);
  return true;
}

async function playAllCompositionTraces() {
  if (!compositionAnimation.data) return;
  cancelCompositionAnimation();
  const runId = compositionAnimation.runId;
  compositionAnimation.playing = true;
  const play = $("#composition-play-all");
  if (play) play.textContent = "Stop";
  for (let i = 0; i < compositionAnimation.data.trace.length; i += 1) {
    if (runId !== compositionAnimation.runId) break;
    const ok = await animateCompositionTrace(i, runId);
    if (!ok) break;
    if (i < compositionAnimation.data.trace.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 260));
    }
  }
  if (runId === compositionAnimation.runId) {
    compositionAnimation.playing = false;
    if (play) play.textContent = "Play all traces";
  }
}

function compositionStep(delta) {
  if (!compositionAnimation.data) return;
  const n = compositionAnimation.data.trace.length;
  const next = Math.max(0, Math.min(n - 1, compositionAnimation.index + delta));
  animateCompositionTrace(next);
}

function renderCompositionAnimation(data) {
  compositionAnimation.data = data;
  compositionAnimation.index = 0;
  const root = $("#composition-animation-root");
  const traceChips = data.trace.map((t, i) => `
    <button class="trace-chip ${i === 0 ? "active" : ""}" data-trace-index="${i}" type="button">
      <span>i = ${t.input}</span><strong>${t.input} → ${t.after_tau} → ${t.result}</strong>
    </button>`).join("");
  root.innerHTML = `
    <article class="panel composition-animation-panel">
      <header class="composition-animation-header">
        <div>
          <p class="eyebrow">COMPOSITION TRACE</p>
          <h2>Watch σ ∘ τ act on every element</h2>
          <p class="muted">Each trace moves through the intermediate value τ(i) before reaching σ(τ(i)).</p>
        </div>
        <div class="composition-controls">
          <button id="composition-prev" class="button" type="button">Previous</button>
          <button id="composition-replay" class="button" type="button">Replay trace</button>
          <button id="composition-next" class="button" type="button">Next</button>
          <button id="composition-play-all" class="button primary" type="button">Play all traces</button>
          <label class="speed-control">Speed
            <select id="composition-speed"><option value="0.65">slow</option><option value="1" selected>normal</option><option value="1.65">fast</option></select>
          </label>
        </div>
      </header>
      <div class="composition-notation-row">
        ${cauchyMatrixHtml(data.tau, "τ")}
        <div class="notation-arrow">then</div>
        ${cauchyMatrixHtml(data.sigma, "σ")}
        <div class="notation-arrow">gives</div>
        ${cauchyMatrixHtml(data.result, "σ ∘ τ")}
      </div>
      <div class="composition-stage-shell">
        <svg id="composition-trace-svg" role="img" aria-label="Animated element-by-element permutation composition"></svg>
      </div>
      <div class="composition-trace-footer">
        <div class="trace-readout">
          <span id="composition-trace-counter" class="trace-counter"></span>
          <div id="composition-current-trace"></div>
        </div>
        <div class="trace-chip-list">${traceChips}</div>
      </div>
      <div class="composition-legend">
        <span><i class="legend-dot input"></i> input</span>
        <span><i class="legend-line tau"></i> first movement under τ</span>
        <span><i class="legend-line sigma"></i> second movement under σ</span>
      </div>
    </article>`;

  $("#composition-prev").addEventListener("click", () => compositionStep(-1));
  $("#composition-next").addEventListener("click", () => compositionStep(1));
  $("#composition-replay").addEventListener("click", () => animateCompositionTrace(compositionAnimation.index));
  $("#composition-play-all").addEventListener("click", () => {
    if (compositionAnimation.playing) cancelCompositionAnimation();
    else playAllCompositionTraces();
  });
  $$(".trace-chip").forEach(chip => chip.addEventListener("click", () => animateCompositionTrace(Number(chip.dataset.traceIndex))));
  renderCompositionDiagram(0);

  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const runId = compositionAnimation.runId;
    compositionAnimation.autoplayTimer = setTimeout(() => {
      compositionAnimation.autoplayTimer = null;
      if (runId === compositionAnimation.runId) playAllCompositionTraces();
    }, 250);
  } else {
    animateCompositionTrace(0);
  }
}

async function composeSelected() {
  cancelCompositionAnimation();
  const requestId = ++compositionAnimation.requestId;
  const sigma = Number($("#sigma-index").value);
  const tau = Number($("#tau-index").value);
  const n = state.n;
  try {
    const data = await api("/api/compose", {
      method: "POST",
      body: JSON.stringify({ n, sigma, tau }),
    });
    if (requestId !== compositionAnimation.requestId || n !== state.n) return;
    const card = (symbol, p, result = false) => `
      <article class="card perm-card ${result ? "result" : ""}">
        <div class="symbol">${symbol} · element #${p.index}</div>
        <div class="cycles code-line">${escapeHtml(p.cycles)}</div>
        <div class="code-line muted">${escapeHtml(p.one_line)}</div>
        <div class="fact-grid"><div class="fact"><span>order</span><strong>${p.order}</strong></div><div class="fact"><span>parity</span><strong>${p.parity}</strong></div></div>
      </article>`;
    $("#compose-result").innerHTML = card("σ", data.sigma) + card("τ", data.tau) + card("σ ∘ τ", data.result, true);
    renderCompositionAnimation(data);
  } catch (error) {
    if (requestId !== compositionAnimation.requestId) return;
    $("#compose-result").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
    $("#composition-animation-root").innerHTML = "";
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

let dihedralLabPromise;
async function loadDihedral() {
  try {
    dihedralLabPromise ||= import("/static/dihedral.js").then(module => module.createDihedralLab(api, escapeHtml, subscriptNumber));
    await (await dihedralLabPromise).load(Number($("#dihedral-m").value));
  } catch (error) {
    $("#dihedral-summary").textContent = error.message;
    setStatus(error.message, "error");
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
  cancelCompositionAnimation();
  compositionAnimation.requestId += 1;
  compositionAnimation.data = null;
  state.n = n;
  $("#compose-result").innerHTML = "";
  $("#composition-animation-root").innerHTML = "";
  await loadGroup();
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
$("#compose-example").addEventListener("click", async () => {
  cancelCompositionAnimation();
  const requestId = ++compositionAnimation.requestId;
  compositionAnimation.data = null;
  if (state.n !== 3) {
    state.n = 3;
    $("#n-input").value = 3;
    await loadGroup();
  }
  if (requestId !== compositionAnimation.requestId || state.n !== 3) return;
  // Lexicographic S3 indices: (231) is #4 and (132) is #2.
  $("#sigma-index").value = 4;
  $("#tau-index").value = 2;
  await composeSelected();
});
$("#load-cayley").addEventListener("click", loadCayley);
$("#load-dihedral").addEventListener("click", loadDihedral);
$("#generate-subgroup").addEventListener("click", generateSubgroup);
$("#load-subgroups").addEventListener("click", loadSubgroups);
$("#load-conjugacy").addEventListener("click", loadConjugacy);

loadGroup().then(loadDihedral).catch(error => setStatus(error.message, "error"));
