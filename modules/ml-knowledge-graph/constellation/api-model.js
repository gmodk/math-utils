/* Rendering adapters. All graph mathematics is computed by the local Python API. */
const api = (path, payload) => {
  const request = new XMLHttpRequest();
  request.open('POST', path, false);
  request.setRequestHeader('Content-Type', 'application/json');
  request.send(JSON.stringify(payload));
  const data = JSON.parse(request.responseText);
  if (request.status >= 400) throw new Error((data.errors || []).map(e => `${e.file || ''}:${e.row || ''} ${e.column || ''}: ${e.message}`).join('\n') || data.detail || 'Local calculation failed');
  return data;
};
const cleanNode = n => Object.fromEntries(Object.entries(n).filter(([k]) => !['_p','layoutTarget'].includes(k)));
const cleanEdge = e => Object.fromEntries(Object.entries(e).filter(([k]) => !['a','b'].includes(k)));
const cleanGraph = g => ({nodes:g.nodes.map(cleanNode),edges:g.edges.map(cleanEdge)});
window.CSVGraphCore = {
  parseCSV(text) { const table=api('/api/csv/parse',{text}); return {...table,warnings:[],_text:text}; },
  inferTable(name, parsed) { const t=api('/api/csv/parse',{name,text:parsed._text}); return {...t,parsed:{...t,warnings:[]}}; },
  normalizeTables(tables) {return api('/api/csv/normalize',{tables:tables.map(t=>({...t,headers:t.parsed.headers,rows:t.parsed.rows,row_numbers:t.parsed.row_numbers}))});},
  inferDisplaySchema(g) {return g.schema || api('/api/graph/schema',cleanGraph(g));},
};
let forcePending=false,forceTime=0,forceEpoch=0;
window.CSVGraphModel = {
  cancelPhysics(){forceEpoch++;},
  components(g,filter){return api('/api/graph/components',{nodes:g.nodes.map(n=>({id:n.id})),edges:g.edges.filter(filter||(()=>true)).map(cleanEdge)});},
  // Stable palette hashing is presentation-only.
  hash(text) {let h=2166136261;for(const ch of String(text)){h^=ch.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;},
  enrich(raw) {
    forceEpoch++;
    const g=api('/api/graph/enrich',raw);g.nodeMap=new Map(g.nodes.map(n=>[n.id,n]));
    g.edges.forEach(e=>{e.a=g.nodeMap.get(e.source);e.b=g.nodeMap.get(e.target);});
    g.getUpstream=id=>new Set(g.nodeMap.get(id)?.upstream||[]);
    g.getDownstream=id=>new Set(g.nodeMap.get(id)?.downstream||[]);
    g.getNeighborhood=id=>new Set([id,...(g.nodeMap.get(id)?.neighborIds||[])]);
    return g;
  },
  clusterTargets(nodes,key){return new Map(Object.entries(api('/api/graph/layout',{graph:{nodes,edges:[]},layout:'cluster',key})));},
  semanticTargets(nodes,key){return new Map(Object.entries(api('/api/graph/layout',{graph:{nodes,edges:[]},layout:'semantic',key})));},
  hierarchicalTargets(nodes){return new Map(Object.entries(api('/api/graph/layout',{graph:{nodes,edges:[]},layout:'hierarchical'})));},
  radialTargets(graph,center){return new Map(Object.entries(api('/api/graph/layout',{graph:cleanGraph(graph),layout:'radial',center})));},
  homeTargets(nodes){return new Map(nodes.map(n=>[n.id,{x:n.homeX,y:n.homeY,z:n.homeZ}]));},
  applyTargets(nodes,targets,immediate){forceEpoch++;nodes.forEach(n=>{const p=targets.get(n.id);if(p){if(immediate)Object.assign(n,p);else n.layoutTarget=p;n.vx=n.vy=n.vz=0;}});},
  transitionStep(nodes,amount){let moving=false;nodes.forEach(n=>{if(!n.layoutTarget)return;const p=n.layoutTarget;for(const k of ['x','y','z'])n[k]+=(p[k]-n[k])*amount;if(Math.abs(p.x-n.x)+Math.abs(p.y-n.y)+Math.abs(p.z-n.z)<.5){Object.assign(n,p);n.layoutTarget=null;}else moving=true;});return moving;},
  forceStep(g,options){
    if(forcePending||performance.now()-forceTime<85)return;
    forcePending=true;forceTime=performance.now();const epoch=forceEpoch;
    const payload={nodes:g.nodes.map(n=>Object.fromEntries(['id','category','x','y','z','vx','vy','vz'].map(k=>[k,n[k]]))),edges:g.edges.map(e=>Object.fromEntries(['source','target','type','weight','forceWeight'].map(k=>[k,e[k]]))),steps:4,options:{...options,relations:Object.fromEntries(options.relations),anchors:Object.fromEntries(options.anchors)}};
    fetch('/api/graph/physics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      .then(r=>{if(!r.ok)throw Error('Physics request failed');return r.json();})
      .then(nodes=>{if(epoch!==forceEpoch)return;nodes.forEach(p=>{const n=g.nodeMap.get(p.id);if(n&&!n._dragging)for(const k of ['x','y','z','vx','vy','vz'])n[k]=p[k];});})
      .catch(error=>{document.getElementById('importStatus').textContent=error.message;})
      .finally(()=>forcePending=false);
  },
};
window.CSVGraphTopology = {
  analyze(nodes,edges,epsilon,fillAreas){
    const r=api('/api/graph/tda',{nodes:nodes.map(n=>({id:n.id})),edges:edges.map(e=>({id:e.id,source:e.source,target:e.target,filterWeight:e.filterWeight})),epsilon,fillAreas});
    r.nodes=nodes;r.edges=edges;
    for(const key of ['mergeEdgeIds','cycleEdgeIds'])r.current[key]=new Set(r.current[key]);
    for(const key of ['rootByNode','componentSizes'])r.current[key]=new Map(Object.entries(r.current[key]));
    for(const key of ['componentColorByNode','componentIndexByNode'])r[key]=new Map(Object.entries(r[key]));
    return r;
  },
};
