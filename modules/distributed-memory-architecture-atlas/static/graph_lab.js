/* Shared Graph / TDA Lab for Distributed Memory Architecture Atlas.
 * Consumes the current approach incidence graph. TDA is an exploratory
 * simplicial overlay and never mutates the Python mathematical model.
 */
(() => {
  'use strict';

  const Q = s => document.querySelector(s);
  const QA = s => [...document.querySelectorAll(s)];
  const palette = ['#65d6c1','#7f8cff','#e8b65b','#d986d6','#7fc6f3','#ef8f8f','#9cd67a','#d1a36d','#ac93ed','#6fd0e7','#d8cf75','#8cc9a3'];

  const lab = {
    graph: null,
    nodes: [],
    edges: [],
    nodeById: new Map(),
    adjacency: new Map(),
    layout: 'force',
    dimension: '2d',
    scope: 'active',
    showLabels: true,
    showFilteredOnly: false,
    physics: true,
    paused: false,
    camera: { zoom: 1, panX: 0, panY: 0, rotX: -0.32, rotY: 0.52, fov: 760 },
    force: { gravity: 0.045, repulsion: 1800, linkStrength: 0.035, linkDistance: 100, damping: 0.88, collision: 19, depth: 0.045 },
    visual: { nodeSize: 8, edgeOpacity: 0.34, labelScale: 1 },
    tda: { enabled: false, threshold: 1, metric: 'approach', maxDim: 3, colorComponents: false, showProjected: false, showSimplices: false, showCycles: false },
    tdaCache: null,
    selectedNode: null,
    hoverNode: null,
    dragNode: null,
    dragStart: null,
    panStart: null,
    rotateStart: null,
    anim: null,
    resizeObserver: null,
    lastTime: 0,
  };

  function canvas(){ return Q('#knowledgeCanvas'); }
  function ctx(){ return canvas()?.getContext('2d'); }
  function nodeKindRank(kind){ return ({coordinate:0,crt:0,anchor:1,data:2,share:2,aggregate:3,spectral:3,stalk:3})[kind] ?? 4; }
  function regionId(n){ return n.id?.startsWith('R') ? Number(n.id.slice(1)) : 0; }
  function isCrt(n){ return n.kind === 'crt' || n.kind === 'coordinate'; }
  function isRegion(n){ return !isCrt(n); }

  async function fetchGraph(){
    const approach = window.Atlas?.currentApproach?.();
    if(!approach || approach === 'comparison') return;
    const active = lab.scope === 'active' ? '1' : '0';
    const q = Number(document.querySelector('#qInput')?.value || .9);
    const data = await window.api(`/api/explore/${encodeURIComponent(approach)}/graph?active=${active}&q=${encodeURIComponent(q)}&limit=1600`);
    setGraph(data.graph);
    const warn=document.querySelector('#graphTruncation');
    if(warn) warn.textContent=data.graph.truncated?`Graph capped at ${data.graph.rendered_regions} of ${data.graph.total_regions} regions for interactive rendering.`:'';
  }

  function setGraph(g){
    const old = new Map(lab.nodes.map(n => [n.id, n]));
    lab.graph = g;
    lab.nodes = g.nodes.map((raw, i) => {
      const prev = old.get(raw.id);
      return {
        ...raw,
        x: prev?.x ?? ((Math.random()-.5)*380),
        y: prev?.y ?? ((Math.random()-.5)*300),
        z: prev?.z ?? ((Math.random()-.5)*260),
        vx: prev?.vx ?? 0,
        vy: prev?.vy ?? 0,
        vz: prev?.vz ?? 0,
        degree: 0,
        component: 0,
        approachFiltration: Number(raw.filtration ?? 0),
        filtration: Number(raw.filtration ?? 0),
      };
    });
    lab.nodeById = new Map(lab.nodes.map(n => [n.id, n]));
    lab.edges = g.edges.map((e, i) => ({...e, id:`E${i}`, sourceNode: lab.nodeById.get(e.source), targetNode: lab.nodeById.get(e.target)})).filter(e=>e.sourceNode&&e.targetNode);
    lab.adjacency = new Map(lab.nodes.map(n=>[n.id, []]));
    lab.edges.forEach(e => { lab.adjacency.get(e.source)?.push(e.target); lab.adjacency.get(e.target)?.push(e.source); e.sourceNode.degree++; e.targetNode.degree++; });
    computeFiltrationScores();
    applyLayout(lab.layout, true);
    updateStats();
    computeTDA();
    fitView();
    startAnimation();
  }

  function computeFiltrationScores(){
    const regs = lab.nodes.filter(isRegion);
    const maxDeg = Math.max(1, ...regs.map(n=>n.degree));
    const maxRid = Math.max(1, ...regs.map(regionId));
    for(const n of regs){
      const k = Math.max(1, n.degree);
      if(lab.tda.metric === 'approach') n.filtration = Math.max(0,Math.min(1,Number(n.approachFiltration||0)));
      else if(lab.tda.metric === 'region-order') n.filtration = regionId(n)/maxRid;
      else if(lab.tda.metric === 'physical-first') n.filtration = (n.active ? 0 : 0.52) + 0.48*(regionId(n)/maxRid);
      else n.filtration = maxDeg <= 1 ? 0 : (k-1)/(maxDeg-1);
    }
    lab.nodes.filter(isCrt).forEach(n=>n.filtration=0);
  }

  function applyLayout(name, hard=false){
    lab.layout = name;
    const nodes = lab.nodes, crt = nodes.filter(isCrt), regs = nodes.filter(isRegion);
    const place = (n,x,y,z=0)=>{ n.x=x;n.y=y;n.z=z;if(hard||name!=='force'){n.vx=n.vy=n.vz=0;} };
    if(name === 'force'){
      if(hard || nodes.every(n=>Math.abs(n.x)<1&&Math.abs(n.y)<1)){
        nodes.forEach((n,i)=>{const a=2*Math.PI*i/Math.max(1,nodes.length);place(n,180*Math.cos(a)+(Math.random()-.5)*30,180*Math.sin(a)+(Math.random()-.5)*30,(Math.random()-.5)*180)});
      }
      lab.physics = true; syncControlValues(); return;
    }
    lab.physics = false;
    if(name === 'hierarchical'){
      const kinds=[...new Set(regs.map(n=>n.kind))]; const groups=[crt,...kinds.map(k=>regs.filter(n=>n.kind===k))].filter(g=>g.length);
      groups.forEach((group,gi)=>{
        const y=-240+gi*(480/Math.max(1,groups.length-1));
        group.sort((a,b)=>a.id.localeCompare(b.id,undefined,{numeric:true})).forEach((n,i)=>place(n,-330+i*(660/Math.max(1,group.length-1)),y,(gi-groups.length/2)*100));
      });
    } else if(name === 'radial'){
      crt.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/Math.max(1,crt.length);place(n,115*Math.cos(a),115*Math.sin(a),0)});
      const kinds=[...new Set(regs.map(n=>n.kind))]; const byKind=kinds.map(k=>regs.filter(n=>n.kind===k)).filter(g=>g.length);
      byKind.forEach((group,gi)=>group.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/Math.max(1,group.length);const r=220+gi*105;place(n,r*Math.cos(a),r*Math.sin(a),(gi-1)*120)}));
    } else if(name === 'circular'){
      const sorted=[...nodes].sort((a,b)=>nodeKindRank(a.kind)-nodeKindRank(b.kind)||a.id.localeCompare(b.id,undefined,{numeric:true}));
      sorted.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/Math.max(1,sorted.length);place(n,310*Math.cos(a),310*Math.sin(a),90*Math.sin(2*a))});
    } else if(name === 'concentric'){
      const groups=[crt,regs.filter(n=>n.active),regs.filter(n=>!n.active)].filter(g=>g.length);
      groups.forEach((group,gi)=>{const r=gi===0?105:210+gi*130;group.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/Math.max(1,group.length);place(n,r*Math.cos(a),r*Math.sin(a),(gi-1)*110)})});
    } else if(name === 'grid'){
      const sorted=[...nodes].sort((a,b)=>nodeKindRank(a.kind)-nodeKindRank(b.kind)||a.id.localeCompare(b.id,undefined,{numeric:true}));
      const cols=Math.ceil(Math.sqrt(sorted.length));
      sorted.forEach((n,i)=>place(n,(i%cols-cols/2)*72,(Math.floor(i/cols)-Math.ceil(sorted.length/cols)/2)*72,((i%3)-1)*70));
    }
    syncControlValues();
    computeTDA();
    fitView();
  }

  function resizeCanvas(){
    const c=canvas(); if(!c) return;
    const rect=c.getBoundingClientRect(); const dpr=window.devicePixelRatio||1;
    const w=Math.max(320,Math.floor(rect.width*dpr)), h=Math.max(360,Math.floor(rect.height*dpr));
    if(c.width!==w||c.height!==h){ c.width=w;c.height=h; c._cssW=rect.width;c._cssH=rect.height; }
  }

  function project(n){
    const c=canvas(); const w=c?._cssW||800,h=c?._cssH||600; let x=n.x,y=n.y,z=n.z;
    if(lab.dimension==='3d'){
      const cy=Math.cos(lab.camera.rotY),sy=Math.sin(lab.camera.rotY),cx=Math.cos(lab.camera.rotX),sx=Math.sin(lab.camera.rotX);
      let x1=x*cy+z*sy, z1=-x*sy+z*cy;
      let y1=y*cx-z1*sx, z2=y*sx+z1*cx;
      const denom=lab.camera.fov+z2; const persp=Math.abs(denom)<1e-9?1e9:lab.camera.fov/denom;
      x=x1*persp; y=y1*persp; z=z2;
    }
    return {x:w/2+lab.camera.panX+x*lab.camera.zoom,y:h/2+lab.camera.panY+y*lab.camera.zoom,z};
  }

  function visibleRegion(n){
    if(!isRegion(n)) return true;
    if(!lab.tda.enabled || !lab.showFilteredOnly) return true;
    return n.filtration <= lab.tda.threshold + 1e-12;
  }

  function render(){
    resizeCanvas(); const c=canvas(), x=ctx(); if(!c||!x) return;
    const dpr=window.devicePixelRatio||1; x.setTransform(dpr,0,0,dpr,0,0); const w=c._cssW||800,h=c._cssH||600;
    x.clearRect(0,0,w,h); x.fillStyle='#12151b'; x.fillRect(0,0,w,h);
    x.save();
    x.strokeStyle='#202631';x.lineWidth=1;
    for(let gx=0;gx<w;gx+=80){x.beginPath();x.moveTo(gx,0);x.lineTo(gx,h);x.stroke();}
    for(let gy=0;gy<h;gy+=80){x.beginPath();x.moveTo(0,gy);x.lineTo(w,gy);x.stroke();}
    x.restore();

    const pos=new Map(lab.nodes.map(n=>[n.id,project(n)]));
    if(lab.tda.enabled && lab.tda.showProjected && lab.tdaCache) drawProjectedComplex(x,pos);

    x.lineWidth=1;
    for(const e of lab.edges){
      if(!visibleRegion(e.sourceNode)||!visibleRegion(e.targetNode)) continue;
      const a=pos.get(e.source),b=pos.get(e.target); if(!a||!b)continue;
      const inc = !lab.tda.enabled || !isRegion(e.targetNode) || e.targetNode.filtration <= lab.tda.threshold+1e-12;
      x.globalAlpha = lab.visual.edgeOpacity*(inc?1:.12); x.strokeStyle='#637083';
      x.beginPath();x.moveTo(a.x,a.y);x.lineTo(b.x,b.y);x.stroke();
    }
    x.globalAlpha=1;

    const sorted=[...lab.nodes].sort((a,b)=>project(a).z-project(b).z);
    for(const n of sorted){
      if(!visibleRegion(n)) continue;
      const p=pos.get(n.id); const selected=lab.selectedNode?.id===n.id; const hover=lab.hoverNode?.id===n.id;
      const base=lab.visual.nodeSize*(isCrt(n)?1.25:1); const r=Math.max(2,base*(selected?1.55:hover?1.25:1));
      let color=nodeColor(n); if(lab.tda.enabled&&lab.tda.colorComponents&&isCrt(n)&&lab.tdaCache) color=palette[(n.component||0)%palette.length];
      x.beginPath();x.arc(p.x,p.y,r,0,Math.PI*2);x.fillStyle=color;x.fill();
      x.lineWidth=selected?3:1.1;x.strokeStyle=selected?'#ffffff':hover?'#e8b65b':'#1a1e25';x.stroke();
      if(lab.showLabels && (lab.camera.zoom>.18 || selected || hover)){
        x.font=`${Math.max(8,10*lab.visual.labelScale)}px ui-monospace, SFMono-Regular, Menlo, monospace`;x.textAlign='left';x.textBaseline='middle';x.fillStyle='#cbd2dc';x.globalAlpha=.9;
        x.fillText(n.label||n.id,p.x+r+4,p.y);x.globalAlpha=1;
      }
    }

    drawOverlay(x,w,h);
  }

  function nodeColor(n){
    if(isCrt(n)) return '#50c7b2';
    if(n.kind==='anchor')return '#e8b65b';
    if(n.kind==='data')return '#6aa4df';
    if(n.kind==='share')return '#6aa4df';
    if(n.kind==='aggregate')return '#7b8cff';
    if(n.kind==='spectral')return n.active?'#987fe7':'#596071';
    if(n.kind==='stalk')return '#d986d6';
    return n.active===false?'#596071':'#8b94a3';
  }

  function drawOverlay(x,w,h){
    x.fillStyle='#0f1218dd';x.fillRect(10,10,220,66);x.strokeStyle='#313846';x.strokeRect(10,10,220,66);
    x.font='10px ui-monospace, SFMono-Regular, Menlo, monospace';x.fillStyle='#b8c0cc';
    x.fillText(`${lab.dimension.toUpperCase()} · ${lab.layout} · ${lab.scope}`,20,28);
    x.fillText(`zoom ${formatZoom(lab.camera.zoom)} · nodes ${lab.nodes.length} · edges ${lab.edges.length}`,20,46);
    x.fillText(lab.physics&&!lab.paused?'physics running':'physics paused',20,64);
  }

  function drawProjectedComplex(x,pos){
    const c=lab.tdaCache; if(!c)return;
    if(lab.tda.showSimplices && lab.tda.maxDim>=2){
      x.globalAlpha=.055; x.fillStyle='#a58cff';
      for(const tri of c.includedTriangles.slice(0,900)){
        const pts=tri.vertices.map(i=>pos.get(`C${i+1}`)); if(pts.some(p=>!p))continue;
        x.beginPath();x.moveTo(pts[0].x,pts[0].y);x.lineTo(pts[1].x,pts[1].y);x.lineTo(pts[2].x,pts[2].y);x.closePath();x.fill();
      }
      x.globalAlpha=1;
    }
    for(const e of c.includedEdges){
      const a=pos.get(`C${e.vertices[0]+1}`),b=pos.get(`C${e.vertices[1]+1}`);if(!a||!b)continue;
      const cyc=c.cycleEdgeKeys.has(e.key);
      x.globalAlpha=cyc&&lab.tda.showCycles?.9:.28; x.strokeStyle=cyc&&lab.tda.showCycles?'#f0b85f':'#5cd5c2'; x.lineWidth=cyc&&lab.tda.showCycles?2.4:1.2; x.setLineDash([4,4]);
      x.beginPath();x.moveTo(a.x,a.y);x.lineTo(b.x,b.y);x.stroke();x.setLineDash([]);
    }
    x.globalAlpha=1;
  }

  function formatZoom(z){
    if(z>=.01&&z<1000) return `${z.toFixed(2)}×`;
    return `${z.toExponential(2)}×`;
  }

  function physicsStep(dt){
    if(!lab.physics||lab.paused||lab.layout!=='force')return;
    const nodes=lab.nodes, N=nodes.length; const sampleAll=N<=650;
    const rep=lab.force.repulsion, g=lab.force.gravity, damping=Math.pow(lab.force.damping,dt*60), coll=lab.force.collision;
    for(const n of nodes){ n.vx += -n.x*g*dt; n.vy += -n.y*g*dt; if(lab.dimension==='3d') n.vz += -n.z*lab.force.depth*dt; }
    if(sampleAll){
      for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){
        const a=nodes[i],b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,dz=lab.dimension==='3d'?a.z-b.z:0;let d2=dx*dx+dy*dy+dz*dz+25;let d=Math.sqrt(d2);let f=rep/d2;
        if(d<coll*2)f+=((coll*2-d)*3);
        dx/=d;dy/=d;dz/=d;a.vx+=dx*f*dt;a.vy+=dy*f*dt;a.vz+=dz*f*dt;b.vx-=dx*f*dt;b.vy-=dy*f*dt;b.vz-=dz*f*dt;
      }
    } else {
      for(let i=0;i<N;i++)for(let k=0;k<24;k++){
        const j=(i*97+k*53)%N;if(i===j)continue;const a=nodes[i],b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,dz=lab.dimension==='3d'?a.z-b.z:0;let d2=dx*dx+dy*dy+dz*dz+25,d=Math.sqrt(d2),f=(rep*N/24)/d2;dx/=d;dy/=d;dz/=d;a.vx+=dx*f*dt;a.vy+=dy*f*dt;a.vz+=dz*f*dt;
      }
    }
    for(const e of lab.edges){
      const a=e.sourceNode,b=e.targetNode;let dx=b.x-a.x,dy=b.y-a.y,dz=lab.dimension==='3d'?b.z-a.z:0;let d=Math.sqrt(dx*dx+dy*dy+dz*dz)||1;const f=(d-lab.force.linkDistance)*lab.force.linkStrength;dx/=d;dy/=d;dz/=d;a.vx+=dx*f*dt;a.vy+=dy*f*dt;a.vz+=dz*f*dt;b.vx-=dx*f*dt;b.vy-=dy*f*dt;b.vz-=dz*f*dt;
    }
    for(const n of nodes){ if(n===lab.dragNode)continue;n.vx*=damping;n.vy*=damping;n.vz*=damping;n.x+=n.vx*dt*60;n.y+=n.vy*dt*60;if(lab.dimension==='3d')n.z+=n.vz*dt*60;else n.z*=.92; }
  }

  function animate(t){
    const dt=Math.min(.033,Math.max(.001,(t-lab.lastTime)/1000||.016));lab.lastTime=t;physicsStep(dt);render();lab.anim=requestAnimationFrame(animate);
  }
  function startAnimation(){ if(lab.anim)return;lab.lastTime=performance.now();lab.anim=requestAnimationFrame(animate); }

  function fitView(){
    if(!lab.nodes.length)return; const c=canvas(); if(!c)return; resizeCanvas();
    const xs=lab.nodes.map(n=>n.x),ys=lab.nodes.map(n=>n.y);const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);const w=c._cssW||800,h=c._cssH||600;
    const sx=(w-100)/Math.max(1,maxX-minX),sy=(h-100)/Math.max(1,maxY-minY);lab.camera.zoom=Math.min(sx,sy);lab.camera.panX=-(minX+maxX)/2*lab.camera.zoom;lab.camera.panY=-(minY+maxY)/2*lab.camera.zoom;updateZoomReadout();
  }
  function resetCamera(){lab.camera={zoom:1,panX:0,panY:0,rotX:-.32,rotY:.52,fov:760};updateZoomReadout();}
  function zoomBy(f){const z=lab.camera.zoom*f;if(Number.isFinite(z)&&z>0)lab.camera.zoom=z;updateZoomReadout();}
  function updateZoomReadout(){const el=Q('#graphZoomReadout');if(el)el.textContent=formatZoom(lab.camera.zoom);}

  function hitTest(mx,my){
    let best=null,bd=Infinity;for(const n of lab.nodes){if(!visibleRegion(n))continue;const p=project(n),d=(p.x-mx)**2+(p.y-my)**2;if(d<bd&&d<Math.max(100,(lab.visual.nodeSize*2.4)**2)){best=n;bd=d;}}return best;
  }

  function canvasPoint(evt){const r=canvas().getBoundingClientRect();return {x:evt.clientX-r.left,y:evt.clientY-r.top};}
  function wireCanvas(){
    const c=canvas(); if(!c)return;
    c.addEventListener('wheel',e=>{e.preventDefault();const p=canvasPoint(e);const before={x:(p.x-(c._cssW||800)/2-lab.camera.panX)/lab.camera.zoom,y:(p.y-(c._cssH||600)/2-lab.camera.panY)/lab.camera.zoom};const factor=Math.exp(-e.deltaY*.0013);zoomBy(factor);if(lab.dimension==='2d'){lab.camera.panX=p.x-(c._cssW||800)/2-before.x*lab.camera.zoom;lab.camera.panY=p.y-(c._cssH||600)/2-before.y*lab.camera.zoom;}},{passive:false});
    c.addEventListener('pointerdown',e=>{c.setPointerCapture(e.pointerId);const p=canvasPoint(e),hit=hitTest(p.x,p.y);if(e.button===2 || (lab.dimension==='3d'&&(e.shiftKey||e.altKey))){lab.rotateStart={x:p.x,y:p.y,rx:lab.camera.rotX,ry:lab.camera.rotY};return;}if(hit){lab.dragNode=hit;lab.selectedNode=hit;updateNodeInfo(hit);if(isRegion(hit)&&window.Atlas?.selectRegion)window.Atlas.selectRegion(regionId(hit));return;}lab.panStart={x:p.x,y:p.y,px:lab.camera.panX,py:lab.camera.panY};});
    c.addEventListener('pointermove',e=>{const p=canvasPoint(e);lab.hoverNode=hitTest(p.x,p.y);if(lab.rotateStart){lab.camera.rotY=lab.rotateStart.ry+(p.x-lab.rotateStart.x)*.007;lab.camera.rotX=lab.rotateStart.rx+(p.y-lab.rotateStart.y)*.007;return;}if(lab.dragNode){const dx=(p.x-(c._cssW||800)/2-lab.camera.panX)/lab.camera.zoom;const dy=(p.y-(c._cssH||600)/2-lab.camera.panY)/lab.camera.zoom;lab.dragNode.x=dx;lab.dragNode.y=dy;lab.dragNode.vx=lab.dragNode.vy=0;return;}if(lab.panStart){lab.camera.panX=lab.panStart.px+p.x-lab.panStart.x;lab.camera.panY=lab.panStart.py+p.y-lab.panStart.y;}});
    const up=()=>{lab.dragNode=null;lab.panStart=null;lab.rotateStart=null;}; c.addEventListener('pointerup',up);c.addEventListener('pointercancel',up);c.addEventListener('contextmenu',e=>e.preventDefault());c.addEventListener('dblclick',fitView);
  }

  function updateNodeInfo(n){
    const el=Q('#graphNodeInfo');if(!el)return;if(!n){el.textContent='Select a graph node.';return;}
    const neighbors=lab.adjacency.get(n.id)||[];
    el.textContent=`${n.id} · ${n.kind}\ndegree: ${n.degree}\nneighbors: ${neighbors.slice(0,18).join(', ')}${neighbors.length>18?' …':''}${isRegion(n)?`\nfiltration: ${n.filtration.toFixed(3)}\nphysical: ${n.active?'yes':'no'}`:''}`;
  }

  function combos(arr,k){
    const out=[];function rec(start,acc){if(acc.length===k){out.push([...acc]);return;}for(let i=start;i<=arr.length-(k-acc.length);i++){acc.push(arr[i]);rec(i+1,acc);acc.pop();}}rec(0,[]);return out;
  }
  function simplexKey(v){return v.join('-');}
  function minBirth(map,key,birth,vertices){const prev=map.get(key);if(!prev||birth<prev.birth)map.set(key,{key,vertices:[...vertices],birth});}

  function buildComplex(){
    const regs=lab.nodes.filter(isRegion); const supports=[];
    for(const r of regs){const ns=(lab.adjacency.get(r.id)||[]).filter(x=>x.startsWith('C')).map(x=>Number(x.slice(1))-1).sort((a,b)=>a-b);if(ns.length>=2)supports.push({region:r,vertices:ns,birth:r.filtration});}
    return window.AtlasTDA.buildComplex(supports,lab.tda.maxDim);
  }

  function topologyAt(complex,t){
    return window.AtlasTDA.topologyAt(complex,lab.nodes.filter(isCrt).length,t,lab.tda.maxDim);
  }

  function computeTDA(){
    if(!lab.nodes.length)return;computeFiltrationScores();const complex=buildComplex();const top=topologyAt(complex,lab.tda.threshold);
    const crt=lab.nodes.filter(isCrt);crt.forEach((n,i)=>n.component=top.components[i]||0);
    lab.tdaCache={complex,includedEdges:top.edges,includedTriangles:top.triangles,includedTetras:top.tetras,cycleEdgeKeys:top.cycleKeys,top};
    updateTdaPanel();renderPersistence(complex);
  }

  function updateTdaPanel(){
    const c=lab.tdaCache;if(!c)return;const t=c.top;
    const set=(id,v)=>{const el=Q(id);if(el)el.textContent=v;};
    set('#tdaBeta0',t.beta0);set('#tdaBeta1',t.beta1);set('#tdaBeta2',t.beta2);set('#tdaBeta3',t.beta3);set('#tdaEdges',t.edges.length);set('#tdaTriangles',t.triangles.length);set('#tdaTetras',t.tetras.length);set('#tdaThresholdValue',lab.tda.threshold.toFixed(2));
    const included=lab.nodes.filter(n=>isRegion(n)&&n.filtration<=lab.tda.threshold+1e-12).length;set('#tdaIncluded',included);
  }

  function renderPersistence(complex){
    const svg=Q('#persistenceSvg');if(!svg)return;const samples=[];for(let i=0;i<=24;i++){const t=i/24;const b=topologyAt(complex,t);samples.push({t,b0:b.beta0,b1:b.beta1,b2:b.beta2,b3:b.beta3});}
    const W=520,H=150,pad=24,maxB=Math.max(1,...samples.flatMap(s=>[s.b0,s.b1,s.b2,s.b3]));const x=t=>pad+t*(W-2*pad),y=v=>H-pad-v/maxB*(H-2*pad);
    const colors=['#65d6c1','#e8b65b','#987fe7','#ef8f8f'];let html=`<line x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${H-pad}" stroke="#4a5261"/><line x1="${pad}" y1="${pad}" x2="${pad}" y2="${H-pad}" stroke="#4a5261"/>`;
    ['b0','b1','b2','b3'].forEach((k,ki)=>{if(ki>lab.tda.maxDim)return;const pts=samples.map(s=>`${x(s.t)},${y(s[k])}`).join(' ');html+=`<polyline points="${pts}" fill="none" stroke="${colors[ki]}" stroke-width="2"/>`;});
    html+=`<line x1="${x(lab.tda.threshold)}" y1="${pad}" x2="${x(lab.tda.threshold)}" y2="${H-pad}" stroke="#fff" stroke-dasharray="3 3" opacity=".7"/><text x="${pad}" y="${H-5}" fill="#7f8997" font-size="9">0</text><text x="${W-pad-5}" y="${H-5}" fill="#7f8997" font-size="9">1</text>`;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML=html;
  }

  function updateStats(){
    const set=(id,v)=>{const el=Q(id);if(el)el.textContent=v;};set('#graphNodeCount',lab.nodes.length);set('#graphEdgeCount',lab.edges.length);set('#graphCrtCount',lab.nodes.filter(isCrt).length);set('#graphRegionCount',lab.nodes.filter(isRegion).length);
  }

  function syncControlValues(){
    const map={ '#layoutSelect':lab.layout,'#dimensionSelect':lab.dimension,'#graphScope':lab.scope,'#graphLabels':lab.showLabels,'#physicsToggle':lab.physics,'#gravitySlider':lab.force.gravity,'#repulsionSlider':lab.force.repulsion,'#linkStrengthSlider':lab.force.linkStrength,'#linkDistanceSlider':lab.force.linkDistance,'#dampingSlider':lab.force.damping,'#collisionSlider':lab.force.collision,'#depthSlider':lab.force.depth,'#nodeSizeSlider':lab.visual.nodeSize,'#edgeOpacitySlider':lab.visual.edgeOpacity,'#labelScaleSlider':lab.visual.labelScale,'#tdaToggle':lab.tda.enabled,'#tdaThreshold':lab.tda.threshold,'#tdaMetric':lab.tda.metric,'#tdaMaxDim':String(lab.tda.maxDim),'#tdaColorComponents':lab.tda.colorComponents,'#tdaProjected':lab.tda.showProjected,'#tdaSimplices':lab.tda.showSimplices,'#tdaCycles':lab.tda.showCycles,'#tdaFilteredOnly':lab.showFilteredOnly};
    for(const [sel,val] of Object.entries(map)){const el=Q(sel);if(!el)continue;if(el.type==='checkbox')el.checked=!!val;else el.value=val;}
    updateZoomReadout();
  }

  function bindControls(){
    const on=(sel,event,fn)=>{const el=Q(sel);if(el)el.addEventListener(event,fn);};
    on('#dimensionSelect','change',e=>{lab.dimension=e.target.value;if(lab.dimension==='2d')lab.nodes.forEach(n=>n.z=0);else if(lab.nodes.every(n=>Math.abs(n.z)<1))lab.nodes.forEach((n,i)=>n.z=((i%7)-3)*45);fitView();});
    on('#layoutSelect','change',e=>applyLayout(e.target.value,true));
    on('#graphScope','change',async e=>{lab.scope=e.target.value;await fetchGraph();});
    on('#graphLabels','change',e=>lab.showLabels=e.target.checked);
    on('#physicsToggle','change',e=>{lab.physics=e.target.checked;if(lab.physics)lab.layout='force';Q('#layoutSelect').value=lab.layout;});
    on('#pausePhysics','click',()=>{lab.paused=!lab.paused;Q('#pausePhysics').textContent=lab.paused?'Resume':'Pause';});
    on('#resetLayout','click',()=>applyLayout(lab.layout,true));on('#fitGraph','click',fitView);on('#resetCamera','click',resetCamera);on('#zoomInGraph','click',()=>zoomBy(1.6));on('#zoomOutGraph','click',()=>zoomBy(1/1.6));
    const sliders=[['#gravitySlider','gravity',Number],['#repulsionSlider','repulsion',Number],['#linkStrengthSlider','linkStrength',Number],['#linkDistanceSlider','linkDistance',Number],['#dampingSlider','damping',Number],['#collisionSlider','collision',Number],['#depthSlider','depth',Number]];
    sliders.forEach(([sel,key,cast])=>on(sel,'input',e=>{lab.force[key]=cast(e.target.value);const v=Q(`${sel}Value`);if(v)v.textContent=e.target.value;}));
    [['#nodeSizeSlider','nodeSize'],['#edgeOpacitySlider','edgeOpacity'],['#labelScaleSlider','labelScale']].forEach(([sel,key])=>on(sel,'input',e=>{lab.visual[key]=Number(e.target.value);const v=Q(`${sel}Value`);if(v)v.textContent=e.target.value;}));
    on('#tdaToggle','change',e=>{lab.tda.enabled=e.target.checked;computeTDA();});
    on('#tdaThreshold','input',e=>{lab.tda.threshold=Number(e.target.value);computeTDA();});
    on('#tdaMetric','change',e=>{lab.tda.metric=e.target.value;computeFiltrationScores();computeTDA();});
    on('#tdaMaxDim','change',e=>{lab.tda.maxDim=Number(e.target.value);computeTDA();});
    on('#tdaColorComponents','change',e=>{lab.tda.colorComponents=e.target.checked;computeTDA();});
    on('#tdaProjected','change',e=>lab.tda.showProjected=e.target.checked);on('#tdaSimplices','change',e=>lab.tda.showSimplices=e.target.checked);on('#tdaCycles','change',e=>lab.tda.showCycles=e.target.checked);on('#tdaFilteredOnly','change',e=>{lab.showFilteredOnly=e.target.checked;computeTDA();});
    on('#graphRefresh','click',fetchGraph);
  }

  function activate(){resizeCanvas();if(!lab.graph)fetchGraph().catch(e=>window.toast?.(e.message,true));else{computeTDA();fitView();}startAnimation();}
  function memoryChanged(){ if(Q('#lab-graph')?.classList.contains('active')) fetchGraph().catch(e=>window.toast?.(e.message,true)); else lab.graph=null; }

  function init(){
    if(!canvas())return;bindControls();wireCanvas();syncControlValues();lab.resizeObserver=new ResizeObserver(()=>resizeCanvas());lab.resizeObserver.observe(canvas());
    window.addEventListener('atlas-experiment-changed',memoryChanged);
    window.addEventListener('atlas-approach-changed',()=>{lab.graph=null; memoryChanged();});
    startAnimation();
  }

  window.GraphLab={activate,refresh:fetchGraph,memoryChanged,fitView,lab};
  init();
})();
