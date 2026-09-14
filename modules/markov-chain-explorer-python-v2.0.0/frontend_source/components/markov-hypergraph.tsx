"use client";

import { useMemo, useRef, useState } from "react";
import type { MarkovNode, Matrix, Transition } from "@/lib/markov";

export type Point = { x: number; y: number; z?: number };

type Props = {
  nodes: MarkovNode[];
  matrix: Matrix;
  transitions: Transition[];
  distribution: number[];
  threshold: number;
  layoutPoints: Record<string, Point>;
  showLabels: boolean;
  showHyperedges: boolean;
  zoom: number;
  camera: { x: number; y: number };
  positions: Record<string, Point>;
  selectedId: string | null;
  targetIds: string[];
  onSelect: (id: string) => void;
  onToggleTarget: (id: string) => void;
  onPositionsChange: (positions: Record<string, Point>) => void;
  onCameraChange: (camera: { x: number; y: number }) => void;
  onZoomChange: (zoom: number) => void;
};

const palette = ["#52e0c4", "#7aa7ff", "#ffbd62", "#f477a6", "#a994ff", "#7fd66c", "#ff7d65"];

function convexHull(points: Point[]): Point[] {
  if (points.length <= 2) return points;
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (o: Point, a: Point, b: Point) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower: Point[] = [];
  sorted.forEach((point) => {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) lower.pop();
    lower.push(point);
  });
  const upper: Point[] = [];
  [...sorted].reverse().forEach((point) => {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) upper.pop();
    upper.push(point);
  });
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

function expandedHull(points: Point[], amount = 24): string {
  const hull = convexHull(points);
  if (hull.length === 1) {
    const p = hull[0];
    return `M ${p.x - amount} ${p.y} A ${amount} ${amount} 0 1 0 ${p.x + amount} ${p.y} A ${amount} ${amount} 0 1 0 ${p.x - amount} ${p.y}`;
  }
  if (hull.length === 2) {
    const [a, b] = hull;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const length = Math.hypot(dx, dy) || 1;
    const nx = -dy / length * amount;
    const ny = dx / length * amount;
    return `M ${a.x + nx} ${a.y + ny} L ${b.x + nx} ${b.y + ny} Q ${b.x + 1.4 * nx} ${b.y + 1.4 * ny} ${b.x - nx} ${b.y - ny} L ${a.x - nx} ${a.y - ny} Q ${a.x - 1.4 * nx} ${a.y - 1.4 * ny} ${a.x + nx} ${a.y + ny} Z`;
  }
  const center = hull.reduce((acc, point) => ({ x: acc.x + point.x / hull.length, y: acc.y + point.y / hull.length }), { x: 0, y: 0 });
  const expanded = hull.map((point) => {
    const length = Math.hypot(point.x - center.x, point.y - center.y) || 1;
    return { x: point.x + amount * (point.x - center.x) / length, y: point.y + amount * (point.y - center.y) / length };
  });
  return `${expanded.map((point, i) => `${i ? "L" : "M"} ${point.x} ${point.y}`).join(" ")} Z`;
}

export function MarkovHypergraph(props: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [panning, setPanning] = useState<{ x: number; y: number; camera: { x: number; y: number } } | null>(null);
  const generated = props.layoutPoints;
  const points = useMemo(() => Object.fromEntries(props.nodes.map((node) => [node.id, props.positions[node.id] ?? generated[node.id] ?? { x: 500, y: 340, z: 0 }])), [props.nodes, props.positions, generated]);
  const index = useMemo(() => new Map(props.nodes.map((node, i) => [node.id, i])), [props.nodes]);
  const visibleTransitions = props.transitions.filter((edge) => edge.enabled && edge.probability >= props.threshold && points[edge.source] && points[edge.target]);
  const viewWidth = 1000 / props.zoom;
  const viewHeight = 680 / props.zoom;
  const viewBox = `${props.camera.x - viewWidth / 2} ${props.camera.y - viewHeight / 2} ${viewWidth} ${viewHeight}`;

  const svgPoint = (event: React.PointerEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const matrix = svg.getScreenCTM();
    return matrix ? point.matrixTransform(matrix.inverse()) : point;
  };

  const handleMove = (event: React.PointerEvent<SVGSVGElement>) => {
    if (dragging) {
      const point = svgPoint(event);
      props.onPositionsChange({ ...props.positions, [dragging]: { x: point.x, y: point.y, z: props.positions[dragging]?.z ?? generated[dragging]?.z ?? 0 } });
    } else if (panning) {
      const scale = 1 / props.zoom;
      props.onCameraChange({ x: panning.camera.x - (event.clientX - panning.x) * scale, y: panning.camera.y - (event.clientY - panning.y) * scale });
    }
  };

  return (
    <svg
      ref={svgRef}
      id="markov-hypergraph-svg"
      role="img"
      aria-label="Interactive weighted state-transition hypergraph"
      viewBox={viewBox}
      className="h-full min-h-[410px] w-full cursor-grab touch-none select-none active:cursor-grabbing"
      onPointerMove={handleMove}
      onPointerUp={() => { setDragging(null); setPanning(null); }}
      onPointerLeave={() => { setDragging(null); setPanning(null); }}
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) setPanning({ x: event.clientX, y: event.clientY, camera: props.camera });
      }}
      onWheel={(event) => {
        event.preventDefault();
        props.onZoomChange(Math.max(0.02, Math.min(10000, props.zoom * Math.exp(-event.deltaY * 0.0012))));
      }}
    >
      <defs>
        <pattern id="micro-grid" width="26" height="26" patternUnits="userSpaceOnUse">
          <path d="M 26 0 L 0 0 0 26" fill="none" stroke="#9bb4b0" strokeOpacity="0.075" strokeWidth="1" />
        </pattern>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
        </marker>
        <filter id="node-glow" x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <rect x={props.camera.x - viewWidth / 2} y={props.camera.y - viewHeight / 2} width={viewWidth} height={viewHeight} fill="url(#micro-grid)" pointerEvents="none" />

      {props.showHyperedges && props.nodes.map((node, sourceIndex) => {
        const members = [node.id, ...props.nodes.flatMap((target, j) => props.matrix[sourceIndex]?.[j] >= props.threshold && sourceIndex !== j ? [target.id] : [])];
        const unique = [...new Set(members)].map((id) => points[id]).filter(Boolean);
        const mass = props.matrix[sourceIndex]?.filter((value) => value >= props.threshold).reduce((sum, value) => sum + value, 0) ?? 0;
        return unique.length ? <path key={`h-${node.id}`} d={expandedHull(unique, 19 + 10 * mass)} fill={palette[sourceIndex % palette.length]} fillOpacity={0.022 + 0.04 * mass} stroke={palette[sourceIndex % palette.length]} strokeOpacity={0.13} strokeWidth={1.2 / props.zoom ** 0.15} strokeDasharray={`${5 / props.zoom ** 0.12} ${7 / props.zoom ** 0.12}`} pointerEvents="none" /> : null;
      })}

      {visibleTransitions.map((edge, edgeIndex) => {
        const a = points[edge.source];
        const b = points[edge.target];
        const reverse = visibleTransitions.some((other) => other.source === edge.target && other.target === edge.source);
        const self = edge.source === edge.target;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const length = Math.hypot(dx, dy) || 1;
        const nx = -dy / length;
        const ny = dx / length;
        const bend = reverse ? (edge.source < edge.target ? 34 : -34) : 12;
        const startX = a.x + dx / length * 28;
        const startY = a.y + dy / length * 28;
        const endX = b.x - dx / length * 32;
        const endY = b.y - dy / length * 32;
        const path = self
          ? `M ${a.x + 18} ${a.y - 18} C ${a.x + 70} ${a.y - 78}, ${a.x - 70} ${a.y - 78}, ${a.x - 18} ${a.y - 18}`
          : `M ${startX} ${startY} Q ${(a.x + b.x) / 2 + nx * bend} ${(a.y + b.y) / 2 + ny * bend} ${endX} ${endY}`;
        const sourceIndex = index.get(edge.source) ?? 0;
        return (
          <g key={`${edge.source}-${edge.target}-${edge.time}-${edgeIndex}`}>
            <path d={path} fill="none" stroke={palette[sourceIndex % palette.length]} strokeOpacity={0.25 + 0.68 * edge.confidence} strokeWidth={(0.8 + 7 * Math.sqrt(edge.probability)) / props.zoom ** 0.13} markerEnd="url(#arrow)" />
            {props.zoom > 0.48 && !self && (
              <text x={(a.x + b.x) / 2 + nx * (bend + 11)} y={(a.y + b.y) / 2 + ny * (bend + 11)} fill="#c7d8d4" fillOpacity="0.72" fontSize={Math.max(9, 12 / props.zoom ** 0.08)} textAnchor="middle" className="font-mono" pointerEvents="none">
                {edge.probability.toFixed(3)}
              </text>
            )}
          </g>
        );
      })}

      {props.nodes.map((node, i) => {
        const point = points[node.id];
        const probability = props.distribution[i] ?? 0;
        const selected = props.selectedId === node.id;
        const target = props.targetIds.includes(node.id);
        const radius = 21 + 13 * Math.sqrt(Math.max(probability, 0));
        return (
          <g
            key={node.id}
            transform={`translate(${point.x} ${point.y})`}
            className="cursor-pointer"
            onPointerDown={(event) => {
              event.stopPropagation();
              if (event.shiftKey) props.onToggleTarget(node.id);
              else { props.onSelect(node.id); setDragging(node.id); }
            }}
          >
            <circle r={radius + 11} fill={palette[i % palette.length]} fillOpacity={selected ? 0.12 : 0.035} filter={selected ? "url(#node-glow)" : undefined} />
            {target && <circle r={radius + 7} fill="none" stroke="#ffbd62" strokeWidth={2.2} strokeDasharray="5 4" />}
            <circle r={radius} fill="#0e1a1d" stroke={palette[i % palette.length]} strokeWidth={selected ? 3 : 1.6} />
            <circle r={Math.max(3, radius * Math.sqrt(probability))} fill={palette[i % palette.length]} fillOpacity={0.86} />
            <text y={4} fill="#eef7f4" fontSize={11} fontWeight={700} textAnchor="middle" pointerEvents="none">{node.label.slice(0, 2).toUpperCase()}</text>
            {props.showLabels && (
              <g pointerEvents="none">
                <rect x={-Math.max(42, node.label.length * 4.7)} y={radius + 10} width={Math.max(84, node.label.length * 9.4)} height={27} rx={8} fill="#091215" fillOpacity={0.9} stroke="#b6cdc8" strokeOpacity={0.12} />
                <text y={radius + 28} fill="#e7f0ee" fontSize={12.5} fontWeight={600} textAnchor="middle">{node.label}</text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}
