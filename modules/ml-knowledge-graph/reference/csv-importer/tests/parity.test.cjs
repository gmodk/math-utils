const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");

test("interface exposes the complete constellation control surface", () => {
  const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
  [
    "layoutSelect", "autoRotate", "captureGraph", "toggleSettings",
    "showSources", "showOutcomes", "csvImportPanel", "categoryFilters", "relationFilters",
    "labels", "local", "home", "fit", "reset", "spread",
    "colorMode", "sizeMode", "clusterMode", "weightMode",
    "physicsToggle", "stir", "relationGravity", "extraGravity", "anchorGravity", "repulsionGravity", "collisionGravity", "labelDensity", "restoreLayout",
    "tdaMode", "areaMode", "epsilon", "tdaKpis", "bettiPlot", "barcodePlot",
    "space", "orientation", "explorerTooltip", "zoomBadge", "inspect", "provenance"
  ].forEach(id => assert.match(html, new RegExp(`id="${id}"`), `missing control ${id}`));
  ["force", "semantic", "hierarchical", "cluster", "radial"].forEach(layout => assert.match(html, new RegExp(`value="${layout}"`)));
});

test("universal import layer contains no Notion ZIP dependency", () => {
  const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
  const app = fs.readFileSync(path.join(root, "src/app.js"), "utf8");
  assert.doesNotMatch(html + app, /JSZip|\.zip|Notion export/i);
  assert.match(app, /universal\.constellation\.graph\.v2/);
  assert.match(app, /apply snapshot/);
});

test("large snapshots use IndexedDB with legacy localStorage compatibility", () => {
  const app = fs.readFileSync(path.join(root, "src/app.js"), "utf8");
  assert.match(app, /indexedDB\.open\(SNAPSHOT_DB/);
  assert.match(app, /writeDatabaseSnapshot/);
  assert.match(app, /readDatabaseSnapshot/);
  assert.match(app, /deleteDatabaseSnapshot/);
  assert.match(app, /localStorage\.getItem\(STORAGE_KEY\)/);
});

test("zoom uses an independent high-range exponential scale", () => {
  const app = fs.readFileSync(path.join(root, "src/app.js"), "utf8");
  assert.match(app, /targetZoom \* Math\.exp/);
  assert.match(app, /Math\.min\(10000/);
  assert.match(app, /perspective \* state\.zoom/);
  assert.doesNotMatch(app, /Math\.min\(1200, state\.targetDist/);
});
