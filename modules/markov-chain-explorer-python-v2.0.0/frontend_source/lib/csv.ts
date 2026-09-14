import type { ChainKind, ChainProject, MarkovNode, Transition, ValidationIssue } from "./markov";

export type ParsedTable = { headers: string[]; rows: Record<string, string>[]; delimiter: string };

export type CsvMapping = {
  recordType: string;
  id: string;
  label: string;
  category: string;
  initial: string;
  reward: string;
  source: string;
  target: string;
  probability: string;
  time: string;
  relation: string;
  confidence: string;
  count: string;
  enabled: string;
};

const aliases: Record<keyof CsvMapping, string[]> = {
  recordType: ["record_type", "recordtype", "type", "kind"],
  id: ["id", "state_id", "stateid", "node_id", "nodeid"],
  label: ["label", "name", "state_label", "statelabel"],
  category: ["category", "class", "group"],
  initial: ["initial_probability", "initial", "pi0", "start_probability"],
  reward: ["reward", "value", "utility"],
  source: ["source", "from", "origin", "state_from"],
  target: ["target", "to", "destination", "state_to"],
  probability: ["probability", "prob", "p", "weight", "transition_probability"],
  time: ["time", "t", "step", "slice"],
  relation: ["relation", "transition_type", "edge_type"],
  confidence: ["confidence", "certainty", "quality"],
  count: ["count", "observations", "frequency", "n"],
  enabled: ["enabled", "active", "status"],
};

function canonical(value: string) {
  return value.trim().toLowerCase().replace(/[\s-]+/g, "_").replace(/[^a-z0-9_]/g, "");
}

export function detectDelimiter(text: string): string {
  const candidates = [",", ";", "\t", "|"];
  const sample = text.split(/\r?\n/).filter(Boolean).slice(0, 6).join("\n");
  let best = ",";
  let bestScore = -1;
  candidates.forEach((delimiter) => {
    let count = 0;
    let quoted = false;
    for (let i = 0; i < sample.length; i += 1) {
      if (sample[i] === '"') quoted = !quoted;
      else if (!quoted && sample[i] === delimiter) count += 1;
    }
    if (count > bestScore) [best, bestScore] = [delimiter, count];
  });
  return best;
}

export function parseCsv(text: string, explicitDelimiter?: string): ParsedTable {
  const delimiter = explicitDelimiter || detectDelimiter(text);
  const records: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];
    if (char === '"') {
      if (quoted && next === '"') {
        field += '"';
        i += 1;
      } else quoted = !quoted;
    } else if (char === delimiter && !quoted) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(field);
      if (row.some((value) => value.trim() !== "")) records.push(row);
      row = [];
      field = "";
    } else field += char;
  }
  row.push(field);
  if (row.some((value) => value.trim() !== "")) records.push(row);
  const headers = (records.shift() ?? []).map((header, i) => header.trim() || `column_${i + 1}`);
  const rows = records.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i]?.trim() ?? ""])));
  return { headers, rows, delimiter };
}

export function detectMapping(headers: string[]): CsvMapping {
  const canonicalHeaders = headers.map((header) => canonical(header));
  const match = (key: keyof CsvMapping) => {
    const index = canonicalHeaders.findIndex((header) => aliases[key].includes(header));
    return index >= 0 ? headers[index] : "";
  };
  return {
    recordType: match("recordType"), id: match("id"), label: match("label"), category: match("category"),
    initial: match("initial"), reward: match("reward"), source: match("source"), target: match("target"),
    probability: match("probability"), time: match("time"), relation: match("relation"),
    confidence: match("confidence"), count: match("count"), enabled: match("enabled"),
  };
}

const numeric = (value: string | undefined, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const boolean = (value: string | undefined, fallback = true) => {
  if (value === undefined || value === "") return fallback;
  return !["false", "0", "off", "no", "disabled", "inactive"].includes(value.toLowerCase());
};

export function projectFromTable(
  table: ParsedTable,
  mapping: CsvMapping,
  kind: ChainKind,
  name = "Imported chain",
): { project: ChainProject; issues: ValidationIssue[] } {
  const issues: ValidationIssue[] = [];
  if (!mapping.source || !mapping.target || !mapping.probability) {
    issues.push({ severity: "error", message: "Map source, target, and probability before applying the CSV." });
  }
  const nodeMap = new Map<string, MarkovNode>();
  const transitions: Transition[] = [];
  const used = new Set(Object.values(mapping).filter(Boolean));
  table.rows.forEach((raw, index) => {
    const rowNumber = index + 2;
    const type = mapping.recordType ? canonical(raw[mapping.recordType] ?? "") : "";
    const explicitNode = type === "node" || type === "state" || (!!mapping.id && !!raw[mapping.id] && !raw[mapping.source]);
    const metadata = Object.fromEntries(Object.entries(raw).filter(([key, value]) => !used.has(key) && value !== ""));
    if (explicitNode) {
      const id = raw[mapping.id]?.trim();
      if (!id) {
        issues.push({ severity: "error", message: "A node row is missing its id.", row: rowNumber });
        return;
      }
      nodeMap.set(id, {
        id,
        label: raw[mapping.label]?.trim() || id,
        category: raw[mapping.category]?.trim() || "state",
        initial: numeric(raw[mapping.initial], 0),
        reward: numeric(raw[mapping.reward], 0),
        metadata,
      });
      return;
    }
    const source = raw[mapping.source]?.trim();
    const target = raw[mapping.target]?.trim();
    if (!source && !target && type) return;
    if (!source || !target) {
      issues.push({ severity: "error", message: "A transition row is missing source or target.", row: rowNumber });
      return;
    }
    const probability = numeric(raw[mapping.probability], Number.NaN);
    if (!Number.isFinite(probability)) issues.push({ severity: "error", message: "A transition probability is not numeric.", row: rowNumber });
    transitions.push({
      source,
      target,
      probability,
      time: Math.max(0, Math.floor(numeric(raw[mapping.time], 0))),
      relation: raw[mapping.relation]?.trim() || "transition",
      confidence: Math.max(0, Math.min(1, numeric(raw[mapping.confidence], 1))),
      count: mapping.count && raw[mapping.count] !== "" ? Math.max(0, numeric(raw[mapping.count], 0)) : undefined,
      enabled: boolean(raw[mapping.enabled], true),
      metadata,
    });
    [source, target].forEach((id) => {
      if (!nodeMap.has(id)) nodeMap.set(id, { id, label: id, category: "state", initial: 0, reward: 0 });
    });
  });
  const nodes = [...nodeMap.values()];
  return { project: { name, kind, nodes, transitions }, issues };
}

function escapeCsv(value: unknown): string {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function projectToCsv(project: ChainProject): string {
  const headers = ["record_type", "id", "label", "category", "initial_probability", "reward", "source", "target", "probability", "time", "relation", "confidence", "count", "enabled"];
  const rows = [headers.join(",")];
  project.nodes.forEach((node) => rows.push([
    "node", node.id, node.label, node.category, node.initial, node.reward, "", "", "", "", "", "", "", "",
  ].map(escapeCsv).join(",")));
  project.transitions.forEach((edge) => rows.push([
    "transition", "", "", "", "", "", edge.source, edge.target, edge.probability, edge.time,
    edge.relation, edge.confidence, edge.count ?? "", edge.enabled,
  ].map(escapeCsv).join(",")));
  return rows.join("\n");
}

export const SAMPLE_CSV = `record_type,id,label,category,initial_probability,reward,source,target,probability,time,relation,confidence,count,enabled
node,nominal,Nominal,stable,1,2,,,,,,,,
node,degraded,Degraded,warning,0,-1,,,,,,,,
node,incident,Incident,critical,0,-8,,,,,,,,
node,recovery,Recovery,transient,0,1,,,,,,,,
node,maintenance,Maintenance,planned,0,-2,,,,,,,,
transition,,,,,,nominal,nominal,0.70,0,operational,0.98,700,true
transition,,,,,,nominal,degraded,0.20,0,operational,0.91,200,true
transition,,,,,,nominal,maintenance,0.10,0,planned,0.95,100,true
transition,,,,,,degraded,nominal,0.25,0,recovery,0.88,250,true
transition,,,,,,degraded,degraded,0.40,0,operational,0.90,400,true
transition,,,,,,degraded,incident,0.25,0,escalation,0.84,250,true
transition,,,,,,degraded,maintenance,0.10,0,planned,0.92,100,true
transition,,,,,,incident,incident,0.35,0,operational,0.86,350,true
transition,,,,,,incident,recovery,0.55,0,recovery,0.91,550,true
transition,,,,,,incident,maintenance,0.10,0,planned,0.93,100,true
transition,,,,,,recovery,nominal,0.55,0,recovery,0.94,550,true
transition,,,,,,recovery,degraded,0.20,0,recovery,0.86,200,true
transition,,,,,,recovery,recovery,0.25,0,operational,0.89,250,true
transition,,,,,,maintenance,nominal,0.75,0,planned,0.96,750,true
transition,,,,,,maintenance,maintenance,0.25,0,planned,0.95,250,true`;

export function sampleProject(): ChainProject {
  const table = parseCsv(SAMPLE_CSV);
  return projectFromTable(table, detectMapping(table.headers), "homogeneous", "System-state chain").project;
}
