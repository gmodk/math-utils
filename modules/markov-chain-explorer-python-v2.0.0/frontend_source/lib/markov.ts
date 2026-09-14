/**
 * Shared browser data contracts only. Numerical Markov-chain work lives in
 * backend/engine.py and is reached through lib/api.ts.
 */
export type ChainKind = "homogeneous" | "nonhomogeneous";
export type LayoutKind = "orbital" | "classes" | "spectral";
export type PoissonBoundary = "cyclic" | "capped";

export type MarkovNode = {
  id: string;
  label: string;
  category: string;
  initial: number;
  reward: number;
  x?: number;
  y?: number;
  z?: number;
  metadata?: Record<string, string | number | boolean>;
};

export type Transition = {
  source: string;
  target: string;
  probability: number;
  time: number;
  relation: string;
  confidence: number;
  count?: number;
  enabled: boolean;
  metadata?: Record<string, string | number | boolean>;
};

export type Matrix = number[][];

export type ChainProject = {
  name: string;
  kind: ChainKind;
  nodes: MarkovNode[];
  transitions: Transition[];
};

export type ValidationIssue = {
  severity: "error" | "warning";
  message: string;
  row?: number;
};

export type ChainAnalysis = {
  stationary: number[];
  recurrentClasses: number[][];
  transientStates: number[];
  absorbingStates: number[];
  irreducible: boolean;
  periods: number[];
  aperiodic: boolean;
  ergodic: boolean;
  entropyRate: number;
  dobrushin: number;
  reversibilizedGap: number;
  rowResidual: number;
};

export function formatProbability(value: number | null, digits = 4): string {
  if (value === null || !Number.isFinite(value)) return "∞";
  if (value > 0 && value < Math.pow(10, -digits)) return value.toExponential(2);
  return value.toFixed(digits);
}
