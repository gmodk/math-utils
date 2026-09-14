import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';

// Rendering transforms only: all group permutations and action axes come from Python.
export class PrismView {
  constructor(container) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#09141e');
    this.camera = new THREE.PerspectiveCamera(38, 1, 0.05, 100);
    this.camera.position.set(3.4, 2.5, 4.5);
    this.renderer = new THREE.WebGLRenderer({antialias:true});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    const canvas = this.renderer.domElement;
    canvas.tabIndex = 0;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Interactive prism. Drag to orbit; pinch or wheel to zoom; right-drag to pan.');
    container.append(canvas);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.minDistance = 2.3;
    this.controls.maxDistance = 18;
    this.controls.listenToKeyEvents(canvas);
    this.controls.saveState();
    this.controls.addEventListener('change', () => this.render());
    canvas.addEventListener('keydown', e => {
      if (['+', '=', '-'].includes(e.key)) { e.preventDefault(); this.zoom(e.key === '-' ? 1.15 : 1/1.15); }
    });
    this.scene.add(new THREE.HemisphereLight(0xbad8ff, 0x24334d, 2.2));
    const light = new THREE.DirectionalLight(0xffffff, 3);
    light.position.set(3, 5, 4); this.scene.add(light);
    const fill = new THREE.DirectionalLight(0x7899ff, 1.3);
    fill.position.set(-3, 1, -4); this.scene.add(fill);
    this.object = new THREE.Group(); this.scene.add(this.object);
    this.axis = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({color:0xe7cc6a}));
    this.scene.add(this.axis);
    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(container);
    this.resize();
  }
  clear() {
    this.object.traverse(o => {
      o.geometry?.dispose();
      const materials = Array.isArray(o.material) ? o.material : [o.material];
      materials.filter(Boolean).forEach(m => { m.map?.dispose(); m.dispose(); });
    });
    this.object.clear();
  }
  build(data, style) {
    this.clear();
    this.data = data; this.style = style;
    const g = data.geometry, positions = [];
    g.faces.forEach(face => {
      for (let i=1; i<face.length-1; i++) [face[0],face[i],face[i+1]].forEach(j => positions.push(...g.prism_vertices[j]));
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.computeVertexNormals();
    this.object.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({color:0x286cad, roughness:0.48, metalness:0.12, side:THREE.DoubleSide})));
    const edgePositions = g.edges.flatMap(edge => edge.flatMap(i => g.prism_vertices[i]));
    const edges = new THREE.BufferGeometry(); edges.setAttribute('position', new THREE.Float32BufferAttribute(edgePositions,3));
    this.object.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({color:0x99c9ff})));
    this.markers = [];
    g.prism_vertices.forEach((p,i) => {
      const marker = new THREE.Mesh(new THREE.SphereGeometry(0.046,12,8), new THREE.MeshStandardMaterial({color:0xb7ddff}));
      marker.position.fromArray(p); this.object.add(marker); this.markers.push(marker);
      // Both ends of a vertical pair bear the same class label; A/B distinguishes endpoints.
      const index = i % data.m, top = i < data.m;
      const textureCanvas = document.createElement('canvas'); textureCanvas.width=128; textureCanvas.height=96;
      const ctx=textureCanvas.getContext('2d');
      ctx.fillStyle='#e9f3ff'; ctx.font='bold 46px Georgia'; ctx.textAlign='center';
      ctx.fillText(g.labels[style][index],64,49); ctx.font='20px sans-serif'; ctx.fillStyle='#9eb2cd'; ctx.fillText(top?'A':'B',64,78);
      const texture = new THREE.CanvasTexture(textureCanvas);
      const label = new THREE.Sprite(new THREE.SpriteMaterial({map:texture, transparent:true, depthTest:true}));
      label.position.set(p[0]*1.22,p[1]*1.2,p[2]*1.22); label.scale.set(.32,.24,1);
      this.object.add(label);
    });
    this.setAction(data.elements[0],1);
  }
  setAction(element, progress) {
    const a = element.animation;
    this.object.quaternion.setFromAxisAngle(new THREE.Vector3(...a.axis_vector), a.angle_rad*progress);
    this.axis.geometry.dispose();
    const axis = new THREE.Vector3(...a.axis_vector);
    this.axis.geometry = new THREE.BufferGeometry().setFromPoints([axis.clone().multiplyScalar(-1.65),axis.clone().multiplyScalar(1.65)]);
    this.axis.visible = element.type === 'reflection';
    this.markers?.forEach((marker,i) => marker.material.color.set(element.permutation[i % this.data.m] !== i % this.data.m ? 0xe7cc6a : 0xb7ddff));
    this.render();
  }
  zoom(factor) {
    const offset = this.camera.position.clone().sub(this.controls.target);
    offset.setLength(THREE.MathUtils.clamp(offset.length()*factor,this.controls.minDistance,this.controls.maxDistance));
    this.camera.position.copy(this.controls.target).add(offset); this.controls.update(); this.render();
  }
  reset() { this.controls.reset(); this.render(); }
  resize() {
    const w=this.container.clientWidth, h=this.container.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w,h); this.camera.aspect=w/h; this.camera.updateProjectionMatrix(); this.render();
  }
  render() { this.renderer.render(this.scene,this.camera); }
}
