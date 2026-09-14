"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, Braces, Calculator, CircleDot, Database, Download, FileJson, FileSpreadsheet,
  FolderOpen, ImageDown, Layers3, Network, RotateCcw, Save, Settings2, Sigma, Target, Trash2, Upload,
} from "lucide-react";
import { Line, LineChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { MarkovHypergraph, type Point } from "@/components/markov-hypergraph";
import { Markov3DGraph } from "@/components/markov-3d-graph";
import {
  formatProbability,
  type ChainKind, type ChainProject, type LayoutKind, type Matrix, type PoissonBoundary,
} from "@/lib/markov";
import { analyzeProject, buildPoissonProject, normalizeProject, type AnalysisResponse } from "@/lib/api";
import {
  detectMapping, parseCsv, projectFromTable, projectToCsv, SAMPLE_CSV, sampleProject, type CsvMapping,
} from "@/lib/csv";

const colors = ["#52e0c4", "#7aa7ff", "#ffbd62", "#f477a6", "#a994ff", "#7fd66c", "#ff7d65", "#51c7ef"];
const snapshotKey = "markov-chain-explorer:snapshots:v1";

type Snapshot = {
  id: string;
  savedAt: string;
  project: ChainProject;
  settings: {
    threshold: number;
    layout: LayoutKind;
    view3d: boolean;
    lambda: number;
    poissonBoundary: PoissonBoundary;
    bayesian: boolean;
    alpha: number;
  };
  positions: Record<string, Point>;
  camera: { x: number; y: number };
};

function downloadText(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

function currentTransitions(project: ChainProject, time: number, relations: string[]) {
  return project.transitions.filter((edge) => edge.enabled && relations.includes(edge.relation) && (project.kind === "homogeneous" || edge.time === time));
}

function niceName(name: string) {
  return name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "markov-chain";
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

function FieldLabel({ children, value }: { children: React.ReactNode; value?: React.ReactNode }) {
  return <div className="field-label"><span>{children}</span>{value && <b>{value}</b>}</div>;
}

export function MarkovLab() {
  const [project, setProject] = useState<ChainProject>(() => sampleProject());
  const [threshold, setThreshold] = useState(0.05);
  const [layout, setLayout] = useState<LayoutKind>("orbital");
  const [view3d, setView3d] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [showHyperedges, setShowHyperedges] = useState(true);
  const [logZoom, setLogZoom] = useState(0);
  const zoom = Math.exp(logZoom);
  const [camera, setCamera] = useState({ x: 500, y: 340 });
  const [positions, setPositions] = useState<Record<string, Point>>({});
  const [selectedId, setSelectedId] = useState<string | null>("nominal");
  const [targetIds, setTargetIds] = useState<string[]>(["incident"]);
  const [selectedTimeIndex, setSelectedTimeIndex] = useState(0);
  const [horizon, setHorizon] = useState(12);
  const [currentStep, setCurrentStep] = useState(4);
  const [discount, setDiscount] = useState(0.95);
  const [pathText, setPathText] = useState("nominal,degraded,incident,recovery,nominal");
  const [lambda, setLambda] = useState(1.4);
  const [poissonBoundary, setPoissonBoundary] = useState<PoissonBoundary>("cyclic");
  const [poissonSlices, setPoissonSlices] = useState(4);
  const [lambdaDrift, setLambdaDrift] = useState(0.12);
  const [bayesian, setBayesian] = useState(false);
  const [alpha, setAlpha] = useState(0.5);
  const [matrixMode, setMatrixMode] = useState<"direct" | "horizon" | "poissonized">("direct");
  const [activeRelations, setActiveRelations] = useState<string[]>([]);
  const [activeCategories, setActiveCategories] = useState<string[]>([]);
  const [status, setStatus] = useState("Example chain loaded");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [engineError, setEngineError] = useState<string | null>(null);

  const [importOpen, setImportOpen] = useState(false);
  const [csvText, setCsvText] = useState(SAMPLE_CSV);
  const parsedCsv = useMemo(() => parseCsv(csvText), [csvText]);
  const [mapping, setMapping] = useState<CsvMapping>(() => detectMapping(parseCsv(SAMPLE_CSV).headers));
  const [importName, setImportName] = useState("Imported chain");
  const [importIssues, setImportIssues] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [snapshotsOpen, setSnapshotsOpen] = useState(false);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);

  useEffect(() => {
    const lifecycle = new AbortController();
    const timer = window.setTimeout(() => {
      analyzeProject({ project, bayesian, alpha, selectedTimeIndex, horizon, currentStep, targetIds, discount, pathText, lambda, threshold })
        .then((next) => {
          if (lifecycle.signal.aborted) return;
          setResult(next);
          setEngineError(null);
        })
        .catch((error: unknown) => {
          if (lifecycle.signal.aborted) return;
          setEngineError(error instanceof Error ? error.message : "The Python numerical engine is unavailable.");
        });
    }, 90);
    return () => { lifecycle.abort(); window.clearTimeout(timer); };
  }, [project, bayesian, alpha, selectedTimeIndex, horizon, currentStep, targetIds, discount, pathText, lambda, threshold]);

  const fallbackMatrix = useMemo<Matrix>(() => project.nodes.map((_, i) => project.nodes.map((__, j) => i === j ? 1 : 0)), [project.nodes]);
  const built = { issues: result?.issues ?? [], times: result?.times ?? [0] };
  const matrices = result?.matrices?.length ? result.matrices : [fallbackMatrix];
  const safeTimeIndex = Math.min(selectedTimeIndex, matrices.length - 1);
  const currentMatrix = result?.currentMatrix ?? matrices[safeTimeIndex];
  const currentTime = result?.currentTime ?? built.times[safeTimeIndex] ?? 0;
  const analysis = useMemo(() => result?.analysis ?? ({
    stationary: project.nodes.map(() => 0), recurrentClasses: [], transientStates: [], absorbingStates: [],
    irreducible: false, periods: [], aperiodic: false, ergodic: false,
    entropyRate: 0, dobrushin: 0, reversibilizedGap: 0, rowResidual: 0,
  }), [result?.analysis, project.nodes]);
  const initial = result?.initial ?? project.nodes.map(() => 0);
  const trajectory = result?.trajectory ?? [initial];
  const displayStep = Math.min(currentStep, trajectory.length - 1);
  const distribution = result?.distribution ?? trajectory[displayStep] ?? initial;
  const hit = result?.hit ?? { probability: 0, firstPassage: [0] };
  const expectedHits = result?.expectedHits ?? project.nodes.map(() => null);
  const reward = result?.reward ?? 0;
  const pathValue = result?.pathValue ?? 0;
  const tda = result?.tda ?? { threshold, beta0: 0, beta1: 0, beta2: 0, edges: 0 };
  const filtration = result?.filtration ?? [];
  const temporal = result?.temporal ?? { slices: matrices.length, maxRowVariation: 0, complete: false };
  const dropout = result?.dropout ?? 0;
  const simulation = result?.simulation ?? project.nodes.map(() => 0);
  const relations = useMemo(() => [...new Set(project.transitions.map((edge) => edge.relation))], [project.transitions]);
  const categories = useMemo(() => [...new Set(project.nodes.map((node) => node.category))], [project.nodes]);

  useEffect(() => {
    const timer = window.setTimeout(() => setActiveRelations((current) => current.length ? current.filter((relation) => relations.includes(relation)).concat(relations.filter((relation) => !current.includes(relation))) : relations), 0);
    return () => window.clearTimeout(timer);
  }, [relations]);
  useEffect(() => {
    const timer = window.setTimeout(() => setActiveCategories((current) => current.length ? current.filter((category) => categories.includes(category)).concat(categories.filter((category) => !current.includes(category))) : categories), 0);
    return () => window.clearTimeout(timer);
  }, [categories]);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      try { setSnapshots(JSON.parse(localStorage.getItem(snapshotKey) || "[]")); } catch { setSnapshots([]); }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const visibleNodes = project.nodes.filter((node) => activeCategories.includes(node.category));
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const filteredEdges = currentTransitions(project, currentTime, activeRelations).filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
  const visibleTransitions = filteredEdges.map((edge) => ({
    ...edge,
    probability: currentMatrix[project.nodes.findIndex((node) => node.id === edge.source)]?.[project.nodes.findIndex((node) => node.id === edge.target)] ?? edge.probability,
  }));
  const visibleMatrix = visibleNodes.map((source) => visibleNodes.map((target) => {
    const active = filteredEdges.some((edge) => edge.source === source.id && edge.target === target.id);
    return active ? currentMatrix[project.nodes.findIndex((node) => node.id === source.id)]?.[project.nodes.findIndex((node) => node.id === target.id)] ?? 0 : 0;
  }));
  const visibleDistribution = visibleNodes.map((node) => distribution[project.nodes.findIndex((candidate) => candidate.id === node.id)] ?? 0);
  const layoutPoints = Object.fromEntries((result?.layouts?.[layout] ?? []).map((point) => [point.id, point]));

  const shownMatrix = matrixMode === "direct"
    ? currentMatrix
    : matrixMode === "poissonized"
      ? result?.poissonizedMatrix ?? currentMatrix
      : result?.horizonMatrix ?? currentMatrix;

  const trajectoryData = trajectory.map((row, step) => Object.fromEntries([
    ["step", step], ...project.nodes.map((node, i) => [node.id, Number(row[i].toFixed(8))]),
  ]));
  const firstPassageData = hit.firstPassage.map((probability, step) => ({ step, probability }));
  const tdaData = filtration.map((point) => ({ threshold: Number(point.threshold.toFixed(2)), beta0: point.beta0, beta1: point.beta1, beta2: point.beta2 }));
  const chartConfig = Object.fromEntries(project.nodes.map((node, i) => [node.id, { label: node.label, color: colors[i % colors.length] }])) satisfies ChartConfig;
  const firstPassageConfig = { probability: { label: "First-passage probability", color: "#ffbd62" } } satisfies ChartConfig;
  const tdaConfig = {
    beta0: { label: "β₀", color: "#52e0c4" }, beta1: { label: "β₁", color: "#7aa7ff" }, beta2: { label: "β₂", color: "#f477a6" },
  } satisfies ChartConfig;

  const changeKind = (kind: ChainKind) => {
    setProject((current) => ({ ...current, kind }));
    setSelectedTimeIndex(0);
    setStatus(kind === "homogeneous" ? "Using one time-invariant transition law" : "Using ordered time-indexed transition laws");
  };

  const generatePoisson = async () => {
    const slices = project.kind === "homogeneous" ? 1 : poissonSlices;
    try {
      const generated = await buildPoissonProject({ project, lambda, boundary: poissonBoundary, slices, drift: lambdaDrift });
      setProject((current) => ({ ...current, transitions: generated.transitions }));
      setActiveRelations(["poisson-count"]);
      setSelectedTimeIndex(0);
      setStatus(`Poisson ${poissonBoundary} chain generated by Python with ${slices} slice${slices === 1 ? "" : "s"}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Poisson generation failed");
    }
  };

  const setMatrixCell = (i: number, j: number, value: number) => {
    if (!Number.isFinite(value) || value < 0) return;
    const source = project.nodes[i]?.id;
    const target = project.nodes[j]?.id;
    setProject((current) => {
      const time = current.kind === "homogeneous" ? 0 : currentTime;
      const rest = current.transitions.filter((edge) => !(edge.source === source && edge.target === target && (current.kind === "homogeneous" || edge.time === time)));
      return { ...current, transitions: [...rest, { source, target, probability: value, time, relation: "matrix-edit", confidence: 1, enabled: true }] };
    });
    setActiveRelations((current) => [...new Set([...current, "matrix-edit"])]);
  };

  const normalizeCurrent = async () => {
    try {
      const normalized = await normalizeProject({ project, selectedTimeIndex: safeTimeIndex, bayesian, alpha });
      setProject((current) => ({ ...current, transitions: normalized.transitions }));
      setActiveRelations(["normalized"]);
      setStatus("Current matrix rows normalized by Python");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Matrix normalization failed");
    }
  };

  const applyImport = async () => {
    const result = projectFromTable(parsedCsv, mapping, project.kind, importName);
    let backendIssues = [] as AnalysisResponse["issues"];
    try {
      const checked = await analyzeProject({
        project: result.project, bayesian, alpha, selectedTimeIndex: 0, horizon, currentStep,
        targetIds: [], discount, pathText, lambda, threshold,
      });
      backendIssues = checked.issues;
    } catch (error) {
      setImportIssues([error instanceof Error ? error.message : "Python validation failed"]);
      return;
    }
    const allIssues = [...result.issues, ...backendIssues];
    const errors = allIssues.filter((issue) => issue.severity === "error");
    if (errors.length) {
      setImportIssues(errors.slice(0, 8).map((issue) => `${issue.row ? `Row ${issue.row}: ` : ""}${issue.message}`));
      return;
    }
    setProject(result.project);
    setPositions({});
    setCamera({ x: 500, y: 340 });
    setSelectedTimeIndex(0);
    setSelectedId(result.project.nodes[0]?.id ?? null);
    setTargetIds(result.project.nodes[1] ? [result.project.nodes[1].id] : []);
    setImportIssues([]);
    setImportOpen(false);
    setStatus(`${result.project.nodes.length} states and ${result.project.transitions.length} transitions imported`);
  };

  const resetExample = () => {
    const sample = sampleProject();
    setProject(sample);
    setPositions({});
    setCamera({ x: 500, y: 340 });
    setLogZoom(0);
    setSelectedTimeIndex(0);
    setSelectedId("nominal");
    setTargetIds(["incident"]);
    setStatus("Example chain restored");
  };

  const saveSnapshot = () => {
    const snapshot: Snapshot = {
      id: `${Date.now()}`,
      savedAt: new Date().toISOString(),
      project,
      settings: { threshold, layout, view3d, lambda, poissonBoundary, bayesian, alpha },
      positions, camera,
    };
    const next = [snapshot, ...snapshots.filter((item) => item.project.name !== project.name)].slice(0, 20);
    localStorage.setItem(snapshotKey, JSON.stringify(next));
    setSnapshots(next);
    setStatus(`Snapshot “${project.name}” saved locally`);
  };

  const loadSnapshot = (snapshot: Snapshot) => {
    setProject(snapshot.project);
    setThreshold(snapshot.settings.threshold);
    setLayout(snapshot.settings.layout);
    setView3d(snapshot.settings.view3d);
    setLambda(snapshot.settings.lambda);
    setPoissonBoundary(snapshot.settings.poissonBoundary);
    setBayesian(snapshot.settings.bayesian);
    setAlpha(snapshot.settings.alpha);
    setPositions(snapshot.positions);
    setCamera(snapshot.camera);
    setSelectedTimeIndex(0);
    setSnapshotsOpen(false);
    setStatus(`Snapshot “${snapshot.project.name}” loaded`);
  };

  const deleteSnapshot = (id: string) => {
    const next = snapshots.filter((snapshot) => snapshot.id !== id);
    localStorage.setItem(snapshotKey, JSON.stringify(next));
    setSnapshots(next);
  };

  const exportPng = () => {
    const webgl = document.getElementById("markov-hypergraph-3d") as HTMLCanvasElement | null;
    if (webgl) {
      webgl.toBlob((blob) => {
        if (!blob) return;
        const output = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = output;
        anchor.download = `${niceName(project.name)}-hypergraph-3d.png`;
        anchor.click();
        URL.revokeObjectURL(output);
      }, "image/png");
      return;
    }
    const svg = document.getElementById("markov-hypergraph-svg") as SVGSVGElement | null;
    if (!svg) return;
    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute("width", "1600");
    clone.setAttribute("height", "1088");
    const data = new XMLSerializer().serializeToString(clone);
    const url = URL.createObjectURL(new Blob([data], { type: "image/svg+xml" }));
    const image = new window.Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 1600;
      canvas.height = 1088;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.fillStyle = "#081114";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const output = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = output;
        anchor.download = `${niceName(project.name)}-hypergraph.png`;
        anchor.click();
        URL.revokeObjectURL(output);
      }, "image/png");
    };
    image.src = url;
  };

  const selectedIndex = project.nodes.findIndex((node) => node.id === selectedId);
  const selectedNode = project.nodes[selectedIndex];
  const selectedOutgoing = selectedIndex >= 0 ? currentMatrix[selectedIndex] : [];
  const curvatureValues = result?.curvatureValues ?? [];

  useEffect(() => {
    const context = typeof document === "undefined" ? undefined : document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const register = (tool: Parameters<typeof context.registerTool>[0]) => {
      try { void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => undefined); } catch { /* unsupported registry */ }
    };
    register({
      name: "read_markov_chain_summary",
      title: "Read Markov chain summary",
      description: "Read the active chain type, states, current transition matrix, and its main finite-state diagnostics without changing the explorer.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: true, untrustedContentHint: false },
      execute: () => ({
        name: project.name,
        kind: project.kind,
        states: project.nodes.map((node) => ({ id: node.id, label: node.label })),
        time: currentTime,
        matrix: currentMatrix,
        diagnostics: {
          irreducible: analysis.irreducible, aperiodic: analysis.aperiodic, ergodic: analysis.ergodic,
          absorbingStates: analysis.absorbingStates.map((i) => project.nodes[i]?.id),
          recurrentClasses: analysis.recurrentClasses.map((component) => component.map((i) => project.nodes[i]?.id)),
          stationary: analysis.stationary,
        },
      }),
    });
    register({
      name: "configure_poisson_chain",
      title: "Build Poisson chain",
      description: "Replace the visible transition law with a Poisson count-driven chain using cyclic or capped boundary behavior.",
      inputSchema: {
        type: "object",
        properties: {
          lambda: { type: "number", minimum: 0, maximum: 100 },
          boundary: { type: "string", enum: ["cyclic", "capped"] },
          slices: { type: "integer", minimum: 1, maximum: 20 },
          lambdaDrift: { type: "number", minimum: -0.9, maximum: 10 },
        },
        required: ["lambda", "boundary"], additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: async (raw) => {
        const input = raw as { lambda?: number; boundary?: PoissonBoundary; slices?: number; lambdaDrift?: number };
        if (!Number.isFinite(input.lambda) || (input.lambda ?? -1) < 0 || !["cyclic", "capped"].includes(input.boundary ?? "")) throw new Error("Invalid Poisson configuration.");
        const sliceCount = project.kind === "homogeneous" ? 1 : Math.max(1, Math.min(20, Math.floor(input.slices ?? poissonSlices)));
        const drift = Math.max(-0.9, input.lambdaDrift ?? lambdaDrift);
        const generated = await buildPoissonProject({ project, lambda: input.lambda!, boundary: input.boundary!, slices: sliceCount, drift });
        setLambda(input.lambda!); setPoissonBoundary(input.boundary!); setPoissonSlices(sliceCount); setLambdaDrift(drift);
        setProject((current) => ({ ...current, transitions: generated.transitions }));
        setActiveRelations(["poisson-count"]); setSelectedTimeIndex(0); setStatus("Poisson chain configured by agent tool");
        return { applied: true, states: project.nodes.length, slices: sliceCount, lambda: input.lambda, boundary: input.boundary };
      },
    });
    register({
      name: "apply_markov_csv",
      title: "Apply Markov CSV",
      description: "Parse, validate, and apply a unified node-and-transition CSV to the explorer. Invalid data leaves the current chain unchanged.",
      inputSchema: {
        type: "object",
        properties: {
          csv: { type: "string", minLength: 1 }, name: { type: "string" },
          kind: { type: "string", enum: ["homogeneous", "nonhomogeneous"] },
        },
        required: ["csv"], additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      execute: async (raw) => {
        const input = raw as { csv?: string; name?: string; kind?: ChainKind };
        if (!input.csv) throw new Error("CSV text is required.");
        const table = parseCsv(input.csv);
        const candidate = projectFromTable(table, detectMapping(table.headers), input.kind ?? project.kind, input.name || "Agent-imported chain");
        const checked = await analyzeProject({
          project: candidate.project, bayesian, alpha, selectedTimeIndex: 0, horizon, currentStep,
          targetIds: [], discount, pathText: "", lambda, threshold,
        });
        const errors = [...candidate.issues, ...checked.issues].filter((issue) => issue.severity === "error");
        if (errors.length) throw new Error(errors.map((issue) => issue.message).join(" "));
        setProject(candidate.project); setPositions({}); setCamera({ x: 500, y: 340 }); setSelectedTimeIndex(0);
        setSelectedId(candidate.project.nodes[0]?.id ?? null); setTargetIds(candidate.project.nodes[1] ? [candidate.project.nodes[1].id] : []);
        setStatus("CSV applied by agent tool");
        return { applied: true, states: candidate.project.nodes.length, transitions: candidate.project.transitions.length };
      },
    });
    register({
      name: "calculate_markov_probability",
      title: "Calculate Markov probability",
      description: "Calculate a future distribution, finite-horizon target hitting probability, or exact path probability for the active chain.",
      inputSchema: {
        type: "object",
        properties: {
          calculation: { type: "string", enum: ["distribution", "hitting", "path"] },
          horizon: { type: "integer", minimum: 0, maximum: 1000 },
          targets: { type: "array", items: { type: "string" } },
          path: { type: "array", items: { type: "string" }, minItems: 1 },
        },
        required: ["calculation"], additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: false },
      execute: async (raw) => {
        const input = raw as { calculation?: string; horizon?: number; targets?: string[]; path?: string[] };
        const steps = Math.max(0, Math.min(1000, Math.floor(input.horizon ?? horizon)));
        const targets = input.targets ?? targetIds;
        const calculated = await analyzeProject({
          project, bayesian, alpha, selectedTimeIndex: safeTimeIndex, horizon: steps, currentStep: steps,
          targetIds: targets, discount, pathText: input.path?.join(",") ?? pathText, lambda, threshold,
        });
        if (input.calculation === "distribution") {
          return { step: steps, distribution: Object.fromEntries(project.nodes.map((node, i) => [node.id, calculated.distribution[i]])) };
        }
        if (input.calculation === "hitting") {
          if (!targets.some((id) => project.nodes.some((node) => node.id === id))) throw new Error("At least one known target state is required.");
          return { horizon: steps, targets, probability: calculated.hit.probability, firstPassage: calculated.hit.firstPassage };
        }
        if (input.calculation === "path") {
          if (!input.path?.length) throw new Error("A non-empty state-id path is required.");
          return { path: input.path, probability: calculated.pathValue };
        }
        throw new Error("Unknown calculation.");
      },
    });
    return () => lifecycle.abort();
  }, [project, currentTime, currentMatrix, analysis, poissonSlices, lambdaDrift, horizon, targetIds, bayesian, alpha, safeTimeIndex, currentStep, discount, pathText, lambda, threshold]);

  return (
    <main className="lab-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
          <div><h1>Markov Chain Explorer</h1><p>stochastic hypergraph laboratory</p></div>
        </div>
        <div className="process-badge"><CircleDot /><span>{project.kind === "homogeneous" ? "Homogeneous" : "Non-homogeneous"}</span><b>{project.nodes.length} states</b></div>
        <div className="top-actions">
          <Button size="sm" variant="ghost" onClick={resetExample}><RotateCcw /> Sample</Button>
          <Button size="sm" variant="ghost" onClick={() => setImportOpen(true)}><Upload /> Import</Button>
          <Button size="sm" variant="ghost" onClick={saveSnapshot}><Save /> Save</Button>
          <Button size="sm" variant="ghost" onClick={() => setSnapshotsOpen(true)}><FolderOpen /> Open</Button>
          <div className="export-menu">
            <Button size="sm" variant="outline"><Download /> Export</Button>
            <div className="export-popover">
              <button onClick={() => downloadText(`${niceName(project.name)}.csv`, projectToCsv(project), "text/csv")}><FileSpreadsheet /> CSV</button>
              <button onClick={() => downloadText(`${niceName(project.name)}.json`, JSON.stringify({ project, matrices, analysis }, null, 2), "application/json")}><FileJson /> JSON</button>
              <button onClick={exportPng}><ImageDown /> PNG</button>
            </div>
          </div>
        </div>
      </header>

      <div className="workspace-grid">
        <aside className="control-rail">
          <section className="rail-section">
            <div className="section-heading"><Activity /><div><h2>Process</h2><p>transition law</p></div></div>
            <div className="segmented">
              <button className={project.kind === "homogeneous" ? "active" : ""} onClick={() => changeKind("homogeneous")}>Homogeneous</button>
              <button className={project.kind === "nonhomogeneous" ? "active" : ""} onClick={() => changeKind("nonhomogeneous")}>Non-homogeneous</button>
            </div>
            {project.kind === "nonhomogeneous" && (
              <label className="field-stack"><FieldLabel value={`t = ${currentTime}`}>Time slice</FieldLabel>
                <Select value={`${safeTimeIndex}`} onValueChange={(value) => setSelectedTimeIndex(Number(value))}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>{built.times.map((time, i) => <SelectItem key={`${time}-${i}`} value={`${i}`}>P({time}) · slice {i + 1}</SelectItem>)}</SelectContent>
                </Select>
              </label>
            )}
            <label className="field-stack"><FieldLabel>Project name</FieldLabel><Input value={project.name} onChange={(event) => setProject((current) => ({ ...current, name: event.target.value }))} /></label>
          </section>

          <section className="rail-section accent-section">
            <div className="section-heading"><Sigma /><div><h2>Poisson builder</h2><p>count-driven transitions</p></div></div>
            <label className="field-stack"><FieldLabel value={`λ = ${lambda.toFixed(2)}`}>Rate parameter</FieldLabel>
              <Slider min={0} max={8} step={0.05} value={[lambda]} onValueChange={([value]) => setLambda(value)} />
            </label>
            <label className="field-stack"><FieldLabel>Boundary rule</FieldLabel>
              <Select value={poissonBoundary} onValueChange={(value) => setPoissonBoundary(value as PoissonBoundary)}>
                <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="cyclic">Cyclic · count modulo n</SelectItem><SelectItem value="capped">Capped · overflow absorbed</SelectItem></SelectContent>
              </Select>
            </label>
            {project.kind === "nonhomogeneous" && <div className="two-fields">
              <label><FieldLabel>Slices</FieldLabel><Input type="number" min={1} max={20} value={poissonSlices} onChange={(event) => setPoissonSlices(Math.max(1, Number(event.target.value)))} /></label>
              <label><FieldLabel>λ drift</FieldLabel><Input type="number" step={0.01} value={lambdaDrift} onChange={(event) => setLambdaDrift(Number(event.target.value))} /></label>
            </div>}
            <Button className="w-full" onClick={generatePoisson}>Build transition law</Button>
            <p className="microcopy">At state i, draw N ~ Poisson(λ). Move by N positions using the selected boundary rule.</p>
          </section>

          <section className="rail-section">
            <div className="section-heading"><Settings2 /><div><h2>Geometry</h2><p>hypergraph controls</p></div></div>
            <label className="field-stack"><FieldLabel>Layout</FieldLabel>
              <Select value={layout} onValueChange={(value) => { setLayout(value as LayoutKind); setPositions({}); }}>
                <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="orbital">Orbital</SelectItem><SelectItem value="classes">Communicating classes</SelectItem><SelectItem value="spectral">Laplacian spectral</SelectItem></SelectContent>
              </Select>
            </label>
            <div className="switch-row"><span>3D projection</span><Switch checked={view3d} onCheckedChange={setView3d} /></div>
            <div className="switch-row"><span>Outgoing hyperedges</span><Switch checked={showHyperedges} onCheckedChange={setShowHyperedges} /></div>
            <div className="switch-row"><span>Adaptive labels</span><Switch checked={showLabels} onCheckedChange={setShowLabels} /></div>
            <label className="field-stack"><FieldLabel value={`p ≥ ${threshold.toFixed(2)}`}>Filtration threshold</FieldLabel><Slider min={0} max={0.95} step={0.01} value={[threshold]} onValueChange={([value]) => setThreshold(value)} /></label>
            <label className="field-stack"><FieldLabel value={`${(zoom * 100).toLocaleString(undefined, { maximumFractionDigits: zoom < 1 ? 2 : 0 })}%`}>Exponential zoom</FieldLabel><Slider min={Math.log(0.02)} max={Math.log(10000)} step={0.01} value={[logZoom]} onValueChange={([value]) => setLogZoom(value)} /></label>
            <Button size="sm" variant="outline" className="w-full" onClick={() => { setLogZoom(0); setCamera({ x: 500, y: 340 }); setPositions({}); }}>Reset camera & positions</Button>
          </section>

          <section className="rail-section">
            <div className="section-heading"><Database /><div><h2>Evidence</h2><p>counts and uncertainty</p></div></div>
            <div className="switch-row"><span>Bayesian smoothing</span><Switch checked={bayesian} onCheckedChange={setBayesian} /></div>
            <label className="field-stack"><FieldLabel value={`α = ${alpha.toFixed(2)}`}>Dirichlet pseudocount</FieldLabel><Slider disabled={!bayesian} min={0.01} max={5} step={0.01} value={[alpha]} onValueChange={([value]) => setAlpha(value)} /></label>
            <p className="microcopy">When counts exist, posterior row means use (nᵢⱼ + α)/(nᵢ· + nα).</p>
          </section>

          {(categories.length > 1 || relations.length > 1) && <section className="rail-section">
            <div className="section-heading"><Layers3 /><div><h2>Visibility</h2><p>categories & relations</p></div></div>
            {categories.map((category) => <label className="check-row" key={category}><Checkbox checked={activeCategories.includes(category)} onCheckedChange={(checked) => setActiveCategories((current) => checked ? [...new Set([...current, category])] : current.filter((item) => item !== category))} /><span>{category}</span></label>)}
            <div className="relation-divider" />
            {relations.map((relation) => <label className="check-row" key={relation}><Checkbox checked={activeRelations.includes(relation)} onCheckedChange={(checked) => setActiveRelations((current) => checked ? [...new Set([...current, relation])] : current.filter((item) => item !== relation))} /><span>{relation}</span></label>)}
          </section>}
        </aside>

        <section className="graph-stage">
          <div className="stage-toolbar">
            <div><h2>{project.name}</h2><p>Shift-click a state to add or remove it from the target set.</p></div>
            <div className="stage-badges"><Badge variant="outline">t = {displayStep}</Badge><Badge variant="outline">β = ({tda.beta0}, {tda.beta1}, {tda.beta2})</Badge><Badge className={analysis.ergodic ? "good-badge" : "warn-badge"}>{analysis.ergodic ? "ergodic" : "non-ergodic"}</Badge></div>
          </div>
          <div className="graph-canvas">
            <div className="canvas-corner"><span>weighted stochastic hypergraph</span><b>{visibleTransitions.filter((edge) => edge.probability >= threshold).length} visible transitions</b></div>
            {view3d ? <Markov3DGraph
              nodes={visibleNodes} matrix={visibleMatrix} transitions={visibleTransitions} distribution={visibleDistribution}
              threshold={threshold} showLabels={showLabels} showHyperedges={showHyperedges} layoutPoints={layoutPoints}
              positions={positions} selectedId={selectedId} targetIds={targetIds}
              onSelect={setSelectedId} onToggleTarget={(id) => setTargetIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])}
              onPositionsChange={setPositions}
            /> : <MarkovHypergraph
              nodes={visibleNodes} matrix={visibleMatrix} transitions={visibleTransitions} distribution={visibleDistribution}
              threshold={threshold} layoutPoints={layoutPoints} showLabels={showLabels} showHyperedges={showHyperedges}
              zoom={zoom} camera={camera} positions={positions} selectedId={selectedId} targetIds={targetIds}
              onSelect={setSelectedId} onToggleTarget={(id) => setTargetIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])}
              onPositionsChange={setPositions} onCameraChange={setCamera} onZoomChange={(value) => setLogZoom(Math.log(value))}
            />}
            <div className="time-scrubber">
              <FieldLabel value={`step ${displayStep} / ${horizon}`}>Probability evolution</FieldLabel>
              <Slider min={0} max={horizon} step={1} value={[displayStep]} onValueChange={([value]) => setCurrentStep(value)} />
            </div>
          </div>
          <div className="stage-footer">
            <div><span className={engineError || built.issues.some((issue) => issue.severity === "error") ? "status-dot error" : "status-dot"} /><p>{engineError ? `Python engine: ${engineError}` : status}</p></div>
            <p>zoom range 2%–1,000,000% · local snapshots · drag states · scroll to zoom</p>
          </div>
        </section>

        <aside className="analysis-rail">
          <Tabs defaultValue="summary" className="h-full">
            <TabsList className="analysis-tabs">
              <TabsTrigger value="summary"><Activity /> Summary</TabsTrigger>
              <TabsTrigger value="matrix"><Braces /> Matrix</TabsTrigger>
              <TabsTrigger value="probability"><Calculator /> Probability</TabsTrigger>
              <TabsTrigger value="topology"><Network /> Structure</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="analysis-content">
              <div className="inspector-title"><div><h2>Chain diagnostics</h2><p>current transition law</p></div><Badge variant="outline">P({currentTime})</Badge></div>
              <div className="metric-grid">
                <Stat label="States" value={`${project.nodes.length}`} note={`${analysis.recurrentClasses.length} closed class${analysis.recurrentClasses.length === 1 ? "" : "es"}`} />
                <Stat label="Entropy rate" value={`${analysis.entropyRate.toFixed(3)} bits`} note="stationary weighted" />
                <Stat label="Spectral gap" value={analysis.reversibilizedGap.toFixed(4)} note="additive reversibilization" />
                <Stat label="Contraction" value={analysis.dobrushin.toFixed(4)} note="Dobrushin coefficient" />
              </div>
              <div className="diagnostic-list">
                <div><span>Irreducible</span><b className={analysis.irreducible ? "positive" : "negative"}>{analysis.irreducible ? "yes" : "no"}</b></div>
                <div><span>Aperiodic recurrent classes</span><b className={analysis.aperiodic ? "positive" : "negative"}>{analysis.aperiodic ? "yes" : "no"}</b></div>
                <div><span>Absorbing states</span><b>{analysis.absorbingStates.length ? analysis.absorbingStates.map((i) => project.nodes[i]?.label).join(", ") : "none"}</b></div>
                <div><span>Row-stochastic residual</span><b>{analysis.rowResidual.toExponential(2)}</b></div>
              </div>
              <div className="panel-block">
                <div className="panel-heading"><h3>Stationary distribution</h3><span>πP = π</span></div>
                <div className="bar-list">{project.nodes.map((node, i) => <div key={node.id}><span>{node.label}</span><div><i style={{ width: `${analysis.stationary[i] * 100}%`, background: colors[i % colors.length] }} /></div><b>{formatProbability(analysis.stationary[i], 3)}</b></div>)}</div>
              </div>
              {selectedNode && <div className="panel-block selected-panel">
                <div className="panel-heading"><h3>{selectedNode.label}</h3><Badge variant="outline">{selectedNode.category}</Badge></div>
                <dl><div><dt>π₀</dt><dd>{formatProbability(initial[selectedIndex])}</dd></div><div><dt>π({displayStep})</dt><dd>{formatProbability(distribution[selectedIndex])}</dd></div><div><dt>reward</dt><dd>{selectedNode.reward.toFixed(2)}</dd></div><div><dt>E[T target]</dt><dd>{formatProbability(expectedHits[selectedIndex], 2)}</dd></div></dl>
                <div className="mini-transitions">{selectedOutgoing.map((value, i) => value > 0 ? <div key={project.nodes[i].id}><span>→ {project.nodes[i].label}</span><b>{formatProbability(value)}</b></div> : null)}</div>
              </div>}
            </TabsContent>

            <TabsContent value="matrix" className="analysis-content">
              <div className="inspector-title"><div><h2>Transition matrix</h2><p>editable stochastic kernel</p></div><Button size="xs" variant="outline" onClick={normalizeCurrent}>Normalize rows</Button></div>
              <div className="segmented matrix-modes"><button className={matrixMode === "direct" ? "active" : ""} onClick={() => setMatrixMode("direct")}>P</button><button className={matrixMode === "horizon" ? "active" : ""} onClick={() => setMatrixMode("horizon")}>{project.kind === "homogeneous" ? `P^${horizon}` : `P₀:${horizon}`}</button><button className={matrixMode === "poissonized" ? "active" : ""} onClick={() => setMatrixMode("poissonized")}>Pλ</button></div>
              <div className="matrix-wrap">
                <Table>
                  <TableHeader><TableRow><TableHead>from \ to</TableHead>{project.nodes.map((node) => <TableHead key={node.id} title={node.label}>{node.label.slice(0, 5)}</TableHead>)}</TableRow></TableHeader>
                  <TableBody>{shownMatrix.map((row, i) => <TableRow key={project.nodes[i]?.id}><TableCell className="row-label">{project.nodes[i]?.label}</TableCell>{row.map((value, j) => <TableCell key={`${i}-${j}`}>{matrixMode === "direct" ? <Input aria-label={`${project.nodes[i]?.label} to ${project.nodes[j]?.label}`} className="matrix-input" type="number" min={0} max={1} step={0.01} key={`${currentTime}-${value}`} defaultValue={value.toFixed(4)} onBlur={(event) => setMatrixCell(i, j, Number(event.target.value))} /> : <span className={value >= threshold ? "matrix-hot" : ""}>{formatProbability(value, 3)}</span>}</TableCell>)}</TableRow>)}</TableBody>
                </Table>
              </div>
              <div className="formula-card"><span>{matrixMode === "poissonized" ? "Poissonized jump count" : project.kind === "homogeneous" ? "Chapman–Kolmogorov" : "Ordered non-homogeneous product"}</span><code>{matrixMode === "poissonized" ? "Pλ = Σₖ e⁻λ λᵏ/k! · Pᵏ" : project.kind === "homogeneous" ? "P(m+n) = PᵐPⁿ" : "P(s,t) = Pₛ Pₛ₊₁ ··· Pₜ₋₁"}</code></div>
              {built.issues.length > 0 && <div className="issue-list"><h3>Validation</h3>{built.issues.slice(0, 8).map((issue, i) => <p key={`${issue.message}-${i}`} className={issue.severity}>{issue.message}</p>)}</div>}
            </TabsContent>

            <TabsContent value="probability" className="analysis-content">
              <div className="inspector-title"><div><h2>Probability laboratory</h2><p>finite-horizon calculations</p></div><Target /></div>
              <label className="field-stack"><FieldLabel value={`${horizon} steps`}>Horizon</FieldLabel><Slider min={1} max={60} step={1} value={[horizon]} onValueChange={([value]) => { setHorizon(value); setCurrentStep((step) => Math.min(step, value)); }} /></label>
              <div className="target-grid"><FieldLabel>Target set</FieldLabel>{project.nodes.map((node) => <label className="check-row" key={node.id}><Checkbox checked={targetIds.includes(node.id)} onCheckedChange={(checked) => setTargetIds((current) => checked ? [...new Set([...current, node.id])] : current.filter((id) => id !== node.id))} /><span>{node.label}</span></label>)}</div>
              <div className="metric-grid"><Stat label="Hit by horizon" value={`${(100 * hit.probability).toFixed(2)}%`} note={`T ≤ ${horizon}`} /><Stat label="Discounted reward" value={reward.toFixed(3)} note={`γ = ${discount.toFixed(2)}`} /></div>
              <label className="field-stack"><FieldLabel value={discount.toFixed(2)}>Reward discount γ</FieldLabel><Slider min={0} max={1} step={0.01} value={[discount]} onValueChange={([value]) => setDiscount(value)} /></label>
              <div className="panel-block chart-block"><div className="panel-heading"><h3>State probabilities</h3><span>π₀P(0,t)</span></div><ChartContainer config={chartConfig} className="h-[230px] w-full aspect-auto"><LineChart data={trajectoryData} accessibilityLayer><CartesianGrid vertical={false} strokeDasharray="3 5" /><XAxis dataKey="step" tickLine={false} axisLine={false} /><YAxis domain={[0, 1]} tickLine={false} axisLine={false} width={34} /><ChartTooltip content={<ChartTooltipContent />} />{project.nodes.slice(0, 8).map((node, i) => <Line key={node.id} dataKey={node.id} stroke={colors[i % colors.length]} strokeWidth={2} dot={false} />)}</LineChart></ChartContainer></div>
              <div className="panel-block chart-block"><div className="panel-heading"><h3>First passage</h3><span>Pr(T = t)</span></div><ChartContainer config={firstPassageConfig} className="h-[180px] w-full aspect-auto"><LineChart data={firstPassageData} accessibilityLayer><CartesianGrid vertical={false} strokeDasharray="3 5" /><XAxis dataKey="step" tickLine={false} axisLine={false} /><YAxis domain={[0, "auto"]} tickLine={false} axisLine={false} width={34} /><ChartTooltip content={<ChartTooltipContent />} /><Line dataKey="probability" stroke="#ffbd62" strokeWidth={2.3} dot={false} /></LineChart></ChartContainer></div>
              <label className="field-stack"><FieldLabel value={`Pr = ${formatProbability(pathValue, 6)}`}>Path probability</FieldLabel><Input value={pathText} onChange={(event) => setPathText(event.target.value)} placeholder="state-a, state-b, state-c" /><small>Use state ids separated by commas or arrows.</small></label>
              <div className="panel-block"><div className="panel-heading"><h3>Monte Carlo occupancy</h3><span>1,600 seeded paths</span></div><div className="bar-list compact">{project.nodes.map((node, i) => <div key={node.id}><span>{node.label}</span><div><i style={{ width: `${simulation[i] * 100}%`, background: colors[i % colors.length] }} /></div><b>{formatProbability(simulation[i], 3)}</b></div>)}</div></div>
            </TabsContent>

            <TabsContent value="topology" className="analysis-content">
              <div className="inspector-title"><div><h2>Structure & topology</h2><p>adapted graph diagnostics</p></div><Network /></div>
              <div className="metric-grid"><Stat label="β₀" value={`${tda.beta0}`} note="connected components" /><Stat label="β₁" value={`${tda.beta1}`} note="independent cycles" /><Stat label="β₂" value={`${tda.beta2}`} note="clique cavities" /><Stat label="Edges" value={`${tda.edges}`} note={`weight ≥ ${threshold.toFixed(2)}`} /></div>
              <div className="panel-block chart-block"><div className="panel-heading"><h3>GF(2) clique filtration</h3><span>threshold 0 → 1</span></div><ChartContainer config={tdaConfig} className="h-[210px] w-full aspect-auto"><LineChart data={tdaData} accessibilityLayer><CartesianGrid vertical={false} strokeDasharray="3 5" /><XAxis dataKey="threshold" tickLine={false} axisLine={false} /><YAxis allowDecimals={false} tickLine={false} axisLine={false} width={28} /><ChartTooltip content={<ChartTooltipContent />} /><Line dataKey="beta0" stroke="#52e0c4" strokeWidth={2} dot={false} /><Line dataKey="beta1" stroke="#7aa7ff" strokeWidth={2} dot={false} /><Line dataKey="beta2" stroke="#f477a6" strokeWidth={2} dot={false} /></LineChart></ChartContainer></div>
              <div className="panel-block"><div className="panel-heading"><h3>Communicating classes</h3><span>SCC decomposition</span></div><div className="class-list">{analysis.recurrentClasses.map((component, i) => <div key={i}><Badge>closed {i + 1}</Badge><span>{component.map((state) => project.nodes[state]?.label).join(" · ")}</span><b>period {analysis.periods[i]}</b></div>)}{analysis.transientStates.length > 0 && <div><Badge variant="outline">transient</Badge><span>{analysis.transientStates.map((state) => project.nodes[state]?.label).join(" · ")}</span></div>}</div></div>
              <div className="metric-grid"><Stat label="Dropout sensitivity" value={dropout.toFixed(4)} note="max stationary TV shift" /><Stat label="Temporal variation" value={temporal.maxRowVariation.toFixed(4)} note={`${temporal.slices} transition slice${temporal.slices === 1 ? "" : "s"}`} /></div>
              <div className="panel-block"><div className="panel-heading"><h3>Forman curvature</h3><span>most negative visible edges</span></div><div className="curvature-list">{curvatureValues.slice(0, 7).map((edge) => <div key={`${edge.i}-${edge.j}`}><span>{project.nodes[edge.i]?.label} → {project.nodes[edge.j]?.label}</span><b>{edge.value.toFixed(3)}</b></div>)}{!curvatureValues.length && <p>No non-loop edge crosses the current threshold.</p>}</div></div>
              <div className="formula-card"><span>Hyperedge semantics</span><code>H(t,i) = {'{'}i{'}'} ∪ supp Pᵗ(i,·)</code><p>Each translucent region collects a source state and every destination reachable above the filtration threshold.</p></div>
            </TabsContent>
          </Tabs>
        </aside>
      </div>

      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent className="import-dialog">
          <DialogHeader><DialogTitle>Import Markov CSV</DialogTitle><DialogDescription>Review the detected schema before replacing the active chain. The current snapshot remains untouched until validation succeeds.</DialogDescription></DialogHeader>
          <div className="import-grid">
            <div className="import-source">
              <div className="import-actions"><Input ref={fileInputRef} type="file" accept=".csv,.tsv,text/csv,text/tab-separated-values" onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                const text = await file.text();
                const table = parseCsv(text);
                setCsvText(text); setMapping(detectMapping(table.headers)); setImportName(file.name.replace(/\.[^.]+$/, "")); setImportIssues([]);
              }} /><Button variant="outline" onClick={() => { setCsvText(SAMPLE_CSV); const table = parseCsv(SAMPLE_CSV); setMapping(detectMapping(table.headers)); }}>Use sample</Button></div>
              <Textarea value={csvText} onChange={(event) => { setCsvText(event.target.value); setMapping(detectMapping(parseCsv(event.target.value).headers)); }} className="csv-editor" spellCheck={false} />
            </div>
            <div className="mapping-panel">
              <label className="field-stack"><FieldLabel>Imported project name</FieldLabel><Input value={importName} onChange={(event) => setImportName(event.target.value)} /></label>
              <div className="mapping-summary"><Stat label="Rows" value={`${parsedCsv.rows.length}`} /><Stat label="Columns" value={`${parsedCsv.headers.length}`} /></div>
              {(["source", "target", "probability", "time", "recordType", "id", "label"] as (keyof CsvMapping)[]).map((key) => <label className="mapping-row" key={key}><span>{key === "recordType" ? "record type" : key}</span><Select value={mapping[key] || "__none__"} onValueChange={(value) => setMapping((current) => ({ ...current, [key]: value === "__none__" ? "" : value }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="__none__">Not mapped</SelectItem>{parsedCsv.headers.map((header) => <SelectItem key={header} value={header}>{header}</SelectItem>)}</SelectContent></Select></label>)}
              <p className="microcopy">Optional recognized fields: category, initial_probability, reward, relation, confidence, count, enabled. Unknown columns are preserved as metadata.</p>
              {importIssues.length > 0 && <div className="issue-list"><h3>Import blocked</h3>{importIssues.map((issue) => <p className="error" key={issue}>{issue}</p>)}</div>}
            </div>
          </div>
          <DialogFooter><DialogClose asChild><Button variant="ghost">Cancel</Button></DialogClose><Button onClick={applyImport}>Validate & apply</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={snapshotsOpen} onOpenChange={setSnapshotsOpen}>
        <DialogContent className="snapshot-dialog">
          <DialogHeader><DialogTitle>Saved projects</DialogTitle><DialogDescription>Snapshots include the chain, camera, node positions, layout, filtration, and stochastic settings.</DialogDescription></DialogHeader>
          <div className="snapshot-list">{snapshots.map((snapshot) => <div key={snapshot.id}><button onClick={() => loadSnapshot(snapshot)}><strong>{snapshot.project.name}</strong><span>{snapshot.project.nodes.length} states · {snapshot.project.kind}</span><small>{new Date(snapshot.savedAt).toLocaleString()}</small></button><Button size="icon-sm" variant="ghost" aria-label={`Delete ${snapshot.project.name}`} onClick={() => deleteSnapshot(snapshot.id)}><Trash2 /></Button></div>)}{!snapshots.length && <div className="empty-state"><FolderOpen /><p>No local snapshots yet.</p></div>}</div>
          <DialogFooter showCloseButton />
        </DialogContent>
      </Dialog>
    </main>
  );
}
