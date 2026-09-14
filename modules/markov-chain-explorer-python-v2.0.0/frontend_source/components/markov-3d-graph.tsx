"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { DragControls } from "three/examples/jsm/controls/DragControls.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import type { MarkovNode, Matrix, Transition } from "@/lib/markov";
import type { Point } from "@/components/markov-hypergraph";

type Props = {
  nodes: MarkovNode[];
  matrix: Matrix;
  transitions: Transition[];
  distribution: number[];
  threshold: number;
  showLabels: boolean;
  showHyperedges: boolean;
  layoutPoints: Record<string, Point>;
  positions: Record<string, Point>;
  selectedId: string | null;
  targetIds: string[];
  onSelect: (id: string) => void;
  onToggleTarget: (id: string) => void;
  onPositionsChange: (positions: Record<string, Point>) => void;
};

const palette = ["#52e0c4", "#7aa7ff", "#ffbd62", "#f477a6", "#a994ff", "#7fd66c", "#ff7d65"];
const toWorld = (point: Point) => new THREE.Vector3((point.x - 500) / 54, -(point.y - 340) / 54, (point.z ?? 0) / 54);
const fromWorld = (point: THREE.Vector3): Point => ({ x: point.x * 54 + 500, y: -point.y * 54 + 340, z: point.z * 54 });

function textSprite(text: string, color = "#eef7f4", scale = 1): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const context = canvas.getContext("2d")!;
  context.fillStyle = "rgba(7, 15, 18, .88)";
  context.roundRect(4, 12, 504, 104, 26);
  context.fill();
  context.strokeStyle = "rgba(182, 205, 200, .18)";
  context.lineWidth = 3;
  context.stroke();
  context.fillStyle = color;
  context.font = "600 42px system-ui, sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, 256, 65, 470);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }));
  sprite.scale.set(3.5 * scale, 0.875 * scale, 1);
  return sprite;
}

export function Markov3DGraph(props: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const cameraMemory = useRef({ position: new THREE.Vector3(0, 4.2, 14), target: new THREE.Vector3() });
  const handlers = useRef({
    select: props.onSelect,
    toggle: props.onToggleTarget,
    move: props.onPositionsChange,
  });
  useEffect(() => {
    handlers.current = { select: props.onSelect, toggle: props.onToggleTarget, move: props.onPositionsChange };
  }, [props.onSelect, props.onToggleTarget, props.onPositionsChange]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x081114, 0.025);
    const camera = new THREE.PerspectiveCamera(46, 1, 0.05, 250);
    camera.position.copy(cameraMemory.current.position);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    } catch {
      host.textContent = "WebGL is unavailable in this browser.";
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.domElement.id = "markov-hypergraph-3d";
    host.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(cameraMemory.current.target);
    controls.enableDamping = true;
    controls.dampingFactor = 0.075;
    controls.minDistance = 2;
    controls.maxDistance = 80;
    controls.zoomToCursor = true;
    controls.addEventListener("change", () => {
      cameraMemory.current = { position: camera.position.clone(), target: controls.target.clone() };
    });

    scene.add(new THREE.HemisphereLight(0xbfefff, 0x071013, 2.4));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.1);
    keyLight.position.set(7, 9, 11);
    scene.add(keyLight);
    const grid = new THREE.GridHelper(30, 30, 0x527d78, 0x203f3c);
    grid.position.y = -4.7;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.16;
    scene.add(grid);

    const points = new Map<string, THREE.Vector3>();
    props.nodes.forEach((node) => points.set(node.id, toWorld(props.positions[node.id] ?? props.layoutPoints[node.id] ?? { x: 500, y: 340, z: 0 })));
    const nodeMeshes: THREE.Mesh[] = [];
    const index = new Map(props.nodes.map((node, i) => [node.id, i]));

    if (props.showHyperedges) {
      props.nodes.forEach((node, sourceIndex) => {
        const memberIds = [node.id, ...props.nodes.flatMap((target, j) => props.matrix[sourceIndex]?.[j] >= props.threshold && sourceIndex !== j ? [target.id] : [])];
        const members = [...new Set(memberIds)].map((id) => points.get(id)).filter((point): point is THREE.Vector3 => Boolean(point));
        if (!members.length) return;
        const center = members.reduce((sum, point) => sum.add(point), new THREE.Vector3()).multiplyScalar(1 / members.length);
        const radius = Math.max(0.72, ...members.map((point) => point.distanceTo(center))) + 0.65;
        const mass = props.matrix[sourceIndex]?.filter((value) => value >= props.threshold).reduce((sum, value) => sum + value, 0) ?? 0;
        const region = new THREE.Mesh(
          new THREE.SphereGeometry(radius, 24, 15),
          new THREE.MeshBasicMaterial({ color: palette[sourceIndex % palette.length], transparent: true, opacity: 0.018 + 0.035 * mass, wireframe: true, depthWrite: false }),
        );
        region.position.copy(center);
        region.scale.y = 0.72;
        scene.add(region);
      });
    }

    const visible = props.transitions.filter((edge) => edge.enabled && edge.probability >= props.threshold && points.has(edge.source) && points.has(edge.target));
    visible.forEach((edge, edgeIndex) => {
      const start = points.get(edge.source)!.clone();
      const end = points.get(edge.target)!.clone();
      const sourceIndex = index.get(edge.source) ?? 0;
      const color = new THREE.Color(palette[sourceIndex % palette.length]);
      if (edge.source === edge.target) {
        const loop = new THREE.Mesh(
          new THREE.TorusGeometry(0.7, 0.018 + 0.07 * Math.sqrt(edge.probability), 8, 40),
          new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.42 + 0.5 * edge.confidence }),
        );
        loop.position.copy(start).add(new THREE.Vector3(0, 0.72, 0));
        loop.rotation.x = Math.PI / 2;
        scene.add(loop);
        return;
      }
      const direction = end.clone().sub(start);
      const normal = direction.clone().cross(new THREE.Vector3(0, 1, 0));
      if (normal.lengthSq() < 1e-6) normal.set(1, 0, 0);
      normal.normalize();
      const reciprocal = visible.some((candidate) => candidate.source === edge.target && candidate.target === edge.source);
      const bend = (reciprocal ? (edge.source < edge.target ? 0.7 : -0.7) : 0.25) + (edgeIndex % 3) * 0.015;
      const control = start.clone().lerp(end, 0.5).addScaledVector(normal, bend).add(new THREE.Vector3(0, 0.18, 0));
      const curve = new THREE.QuadraticBezierCurve3(start, control, end);
      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 24, 0.018 + 0.055 * Math.sqrt(edge.probability), 7, false),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.28 + 0.58 * edge.confidence }),
      );
      scene.add(tube);
      const tip = curve.getPoint(0.91);
      const tangent = curve.getTangent(0.91).normalize();
      const cone = new THREE.Mesh(
        new THREE.ConeGeometry(0.10 + 0.08 * Math.sqrt(edge.probability), 0.34, 10),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.86 }),
      );
      cone.position.copy(tip);
      cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      scene.add(cone);
      if (props.showLabels) {
        const label = textSprite(edge.probability.toFixed(3), "#c7d8d4", 0.48);
        label.position.copy(curve.getPoint(0.52)).add(new THREE.Vector3(0, 0.22, 0));
        scene.add(label);
      }
    });

    props.nodes.forEach((node, i) => {
      const probability = props.distribution[i] ?? 0;
      const radius = 0.39 + 0.22 * Math.sqrt(Math.max(probability, 0));
      const selected = props.selectedId === node.id;
      const target = props.targetIds.includes(node.id);
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 32, 22),
        new THREE.MeshStandardMaterial({
          color: palette[i % palette.length], emissive: palette[i % palette.length],
          emissiveIntensity: selected ? 0.9 : 0.25 + probability * 0.8,
          roughness: 0.3, metalness: 0.12,
        }),
      );
      mesh.position.copy(points.get(node.id)!);
      mesh.userData.stateId = node.id;
      scene.add(mesh);
      nodeMeshes.push(mesh);
      if (target) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(radius + 0.16, 0.025, 8, 48),
          new THREE.MeshBasicMaterial({ color: 0xffbd62, transparent: true, opacity: 0.9 }),
        );
        ring.rotation.x = Math.PI / 2;
        mesh.add(ring);
      }
      if (props.showLabels) {
        const label = textSprite(node.label);
        label.position.copy(mesh.position).add(new THREE.Vector3(0, radius + 0.58, 0));
        scene.add(label);
      }
    });

    const drag = new DragControls(nodeMeshes, camera, renderer.domElement);
    drag.addEventListener("dragstart", () => { controls.enabled = false; });
    drag.addEventListener("dragend", (event) => {
      controls.enabled = true;
      const object = event.object as THREE.Object3D;
      const id = object.userData.stateId as string | undefined;
      if (id) handlers.current.move({ ...props.positions, [id]: fromWorld(object.position) });
    });

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let pointerStart: { x: number; y: number } | null = null;
    const pointerDown = (event: PointerEvent) => { pointerStart = { x: event.clientX, y: event.clientY }; };
    const pointerUp = (event: PointerEvent) => {
      if (!pointerStart || Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y) > 5) return;
      const bounds = renderer.domElement.getBoundingClientRect();
      pointer.set((event.clientX - bounds.left) / bounds.width * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(nodeMeshes, false)[0];
      const id = hit?.object.userData.stateId as string | undefined;
      if (id) {
        if (event.shiftKey) handlers.current.toggle(id);
        else handlers.current.select(id);
      }
    };
    renderer.domElement.addEventListener("pointerdown", pointerDown);
    renderer.domElement.addEventListener("pointerup", pointerUp);

    const resize = () => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();
    let frame = 0;
    const render = () => {
      frame = requestAnimationFrame(render);
      controls.update();
      renderer.render(scene, camera);
    };
    render();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      renderer.domElement.removeEventListener("pointerdown", pointerDown);
      renderer.domElement.removeEventListener("pointerup", pointerUp);
      drag.dispose();
      controls.dispose();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) object.geometry.dispose();
        const material = (object as THREE.Mesh).material;
        if (Array.isArray(material)) material.forEach((item) => item.dispose());
        else material?.dispose();
        if (object instanceof THREE.Sprite) object.material.map?.dispose();
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [props.nodes, props.matrix, props.transitions, props.distribution, props.threshold, props.showLabels, props.showHyperedges, props.layoutPoints, props.positions, props.selectedId, props.targetIds]);

  return <div ref={hostRef} className="h-full min-h-[410px] w-full cursor-grab touch-none active:cursor-grabbing" role="img" aria-label="Interactive three-dimensional weighted state-transition hypergraph; drag to rotate, scroll to zoom, and right-drag to pan" />;
}
