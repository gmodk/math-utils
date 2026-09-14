import type {
  ChainAnalysis,
  ChainProject,
  LayoutKind,
  Matrix,
  PoissonBoundary,
  Transition,
  ValidationIssue,
} from "./markov";

export type Point3D = { id: string; x: number; y: number; z: number };

export type AnalysisResponse = {
  issues: ValidationIssue[];
  times: number[];
  matrices: Matrix[];
  currentMatrix: Matrix;
  currentTime: number;
  analysis: ChainAnalysis;
  initial: number[];
  trajectory: number[][];
  distribution: number[];
  hit: { probability: number; firstPassage: number[] };
  expectedHits: Array<number | null>;
  reward: number;
  pathValue: number;
  tda: { threshold: number; beta0: number; beta1: number; beta2: number; edges: number };
  filtration: Array<{ threshold: number; beta0: number; beta1: number; beta2: number; edges: number }>;
  temporal: { slices: number; maxRowVariation: number; complete: boolean };
  dropout: number;
  simulation: number[];
  curvatureValues: Array<{ i: number; j: number; value: number }>;
  horizonMatrix: Matrix;
  poissonizedMatrix: Matrix;
  layouts: Record<LayoutKind, Point3D[]>;
};

export type AnalysisInput = {
  project: ChainProject;
  bayesian: boolean;
  alpha: number;
  selectedTimeIndex: number;
  horizon: number;
  currentStep: number;
  targetIds: string[];
  discount: number;
  pathText: string;
  lambda: number;
  threshold: number;
};

async function requestJson<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload && typeof payload === "object" && "detail" in payload && typeof payload.detail === "string"
      ? payload.detail
      : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  return payload as T;
}

export function analyzeProject(input: AnalysisInput): Promise<AnalysisResponse> {
  return requestJson<AnalysisResponse>("/api/analyze", input);
}

export function buildPoissonProject(input: {
  project: ChainProject;
  lambda: number;
  boundary: PoissonBoundary;
  slices: number;
  drift: number;
}): Promise<{ transitions: Transition[]; matrices: Matrix[]; lambdaSchedule: number[] }> {
  return requestJson("/api/poisson", input);
}

export function normalizeProject(input: {
  project: ChainProject;
  selectedTimeIndex: number;
  bayesian: boolean;
  alpha: number;
}): Promise<{ transitions: Transition[]; matrix: Matrix; time: number }> {
  return requestJson("/api/normalize", input);
}
