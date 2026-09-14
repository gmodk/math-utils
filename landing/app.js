const grid = document.querySelector("#module-grid");
const systemState = document.querySelector(".system-state");
const systemLabel = document.querySelector("#system-label");
const accents = ["#52e0c4", "#7aa7ff", "#a994ff", "#ffbd62"];
let previousModules = "";

function renderModules(modules) {
  grid.replaceChildren();
  modules.forEach((module, index) => {
    const card = document.createElement("article");
    card.className = "module-card";
    card.style.setProperty("--accent", accents[index % accents.length]);

    const number = document.createElement("div");
    number.className = "module-number";
    number.textContent = String(index + 1).padStart(2, "0");

    const title = document.createElement("h3");
    title.textContent = module.title;

    const description = document.createElement("p");
    description.textContent = module.description;

    const foot = document.createElement("div");
    foot.className = "card-foot";

    const readiness = document.createElement("span");
    readiness.className = `readiness${module.ready ? " ready" : ""}`;
    readiness.textContent = module.ready ? "Ready" : "Unavailable";

    const link = document.createElement("a");
    link.className = "open-link";
    link.href = `http://${window.location.hostname}:${module.port}/`;
    link.target = "_blank";
    link.rel = "noopener";
    link.setAttribute("aria-label", `Open ${module.title}`);
    link.append("Open explorer ");
    const arrow = document.createElement("span");
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    link.append(arrow);

    foot.append(readiness, link);
    card.append(number, title, description, foot);
    grid.append(card);
  });
  grid.setAttribute("aria-busy", "false");
}

async function refreshStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    const data = await response.json();
    const snapshot = JSON.stringify(data.modules);
    if (snapshot !== previousModules) {
      const focusedLabel = document.activeElement?.getAttribute("aria-label");
      renderModules(data.modules);
      if (focusedLabel) {
        Array.from(grid.querySelectorAll("a")).find((link) => link.getAttribute("aria-label") === focusedLabel)?.focus();
      }
      previousModules = snapshot;
    }
    const readyCount = data.modules.filter((module) => module.ready).length;
    const allReady = readyCount === data.modules.length;
    systemState.classList.toggle("ready", allReady);
    systemState.classList.toggle("partial", !allReady);
    systemLabel.textContent = allReady
      ? "All modules ready"
      : `${readyCount}/${data.modules.length} modules ready`;
    return allReady;
  } catch (error) {
    systemState.classList.remove("ready");
    systemState.classList.add("partial");
    systemLabel.textContent = "Status unavailable";
    return false;
  }
}

async function beginStatusLoop() {
  const ready = await refreshStatus();
  window.setTimeout(beginStatusLoop, ready ? 5000 : 1200);
}

beginStatusLoop();
