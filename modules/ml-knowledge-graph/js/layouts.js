import {localJSON} from './api.js';
function positions(nodes,edges,layout,center){return new Map(Object.entries(localJSON('/api/fork/layout',{nodes,edges,layout,center})));}
export function computeForceLayout(nodes,edges){return positions(nodes,edges,'force');}
export function computeHierarchicalLayout(nodes){return positions(nodes,[],'hierarchical');}
export function computeClusterLayout(nodes){return positions(nodes,[],'cluster');}
export function computeRadialLayout(nodes,centerId,nodeMap){return positions(nodes,[],'radial',centerId);}
// --- Layout transition animation ---

function smootherStep(t) {
  return t * t * t * (t * (t * 6 - 15) + 10);
}

export function animateToPositions(nodes, targetPositions, onUpdate, duration = 900) {
  return new Promise(resolve => {
    const starts = new Array(nodes.length);
    const targets = new Array(nodes.length);

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      starts[i] = { x: node.x, y: node.y, z: node.z };
      targets[i] = targetPositions.get(node.id) || starts[i];
    }

    const t0 = performance.now();
    let frame = 0;

    function step(time) {
      const t = Math.min((time - t0) / duration, 1);
      const eased = smootherStep(t);

      for (let i = 0; i < nodes.length; i++) {
        const start = starts[i];
        const target = targets[i];
        nodes[i].x = start.x + (target.x - start.x) * eased;
        nodes[i].y = start.y + (target.y - start.y) * eased;
        nodes[i].z = start.z + (target.z - start.z) * eased;
      }

      frame += 1;
      onUpdate({ frame, progress: t, isFinalFrame: t >= 1 });

      if (t < 1) {
        requestAnimationFrame(step);
        return;
      }

      for (let i = 0; i < nodes.length; i++) {
        const target = targets[i];
        nodes[i].x = target.x;
        nodes[i].y = target.y;
        nodes[i].z = target.z;
      }

      resolve();
    }

    requestAnimationFrame(step);
  });
}
