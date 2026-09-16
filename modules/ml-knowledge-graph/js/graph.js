import {localJSON,csvSnapshot} from './api.js';
// Graph data loading, derived property computation, and graph algorithms

// --- Category color system ---
// Each unique category gets a distinct hue. We assign hues after loading
// based on sorted category names for stable, well-spaced hues.

let categoryColorMap = new Map(); // category → { h, s, l } (all normalized 0-1)
let sortedCategories = [];        // categories sorted alphabetically
const CATEGORY_HUE_OFFSET_DEGREES = 14;
const CATEGORY_SATURATION_STEPS = [0.84, 0.9, 0.87, 0.92];
const CATEGORY_LIGHTNESS_STEPS = [0.6, 0.56, 0.64, 0.58, 0.62];
const DEFAULT_CATEGORY_COLOR = { h: 0.54, s: 0.78, l: 0.58 };

export function getCategoryColor(category) {
  const color = categoryColorMap.get(category);
  if (color) return color;
  return DEFAULT_CATEGORY_COLOR; // fallback for unknown
}

export function getCategoryColorHex(category) {
  const { h, s, l } = getCategoryColor(category);
  return hslToHex(h, s, l);
}

export function getSortedCategories() { return sortedCategories; }

function hslToHex(h, s, l) {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h * 6) % 2 - 1));
  const m = l - c / 2;
  let r, g, b;
  const sector = Math.floor(h * 6) % 6;
  switch (sector) {
    case 0: r = c; g = x; b = 0; break;
    case 1: r = x; g = c; b = 0; break;
    case 2: r = 0; g = c; b = x; break;
    case 3: r = 0; g = x; b = c; break;
    case 4: r = x; g = 0; b = c; break;
    case 5: r = c; g = 0; b = x; break;
    default: r = 0; g = 0; b = 0;
  }
  const toHex = v => Math.round((v + m) * 255).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// --- Data loading ---

export async function loadGraph(url='knowledge_graph.json') {
  const raw=await csvSnapshot();
  const data=raw||await (await fetch(url)).json();
  const graph=localJSON('/api/fork/graph',{graph:data});
  graph.nodeMap=new Map(graph.nodes.map(n=>[n.id,n]));buildCategoryColorMap(graph.nodes);
  return graph;
}

// --- Derived property computation ---

function buildCategoryColorMap(nodes) {
  const categorySet = new Set();
  for (const node of nodes) {
    if (node.category) categorySet.add(node.category);
  }

  sortedCategories = [...categorySet].sort();
  categoryColorMap = new Map();
  const count = sortedCategories.length || 1;
  sortedCategories.forEach((cat, i) => {
    const hueDegrees = ((i * 360 / count) + CATEGORY_HUE_OFFSET_DEGREES) % 360;
    const saturation = CATEGORY_SATURATION_STEPS[i % CATEGORY_SATURATION_STEPS.length];
    const lightness = CATEGORY_LIGHTNESS_STEPS[i % CATEGORY_LIGHTNESS_STEPS.length];
    categoryColorMap.set(cat, {
      h: hueDegrees / 360,
      s: saturation,
      l: lightness,
    });
  });
}

export function getUpstream(nodeId,nodeMap){return new Set(nodeMap.get(nodeId)?.upstream||[]);}
export function getDownstream(nodeId,nodeMap){return new Set(nodeMap.get(nodeId)?.downstream||[]);}
