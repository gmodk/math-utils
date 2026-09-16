// The unchanged supplied implementation is the oracle, never the runtime engine.
const fs=require('node:fs');
const Model=require('../reference/csv-importer/src/graph-core.js');
const T=require('../reference/csv-importer/src/topology.js');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const g=Model.enrich(input.graph);g.edges.forEach(e=>e.filterWeight=e.weight);
g.edges.sort((a,b)=>a.filterWeight-b.filterWeight||a.id.localeCompare(b.id));
function clean(value){
 if(value instanceof Map)return Object.fromEntries([...value].map(([k,v])=>[k,clean(v)]));
 if(value instanceof Set)return [...value];
 if(Array.isArray(value))return value.map(clean);
 if(value&&typeof value==='object'){
  if(value.vertices&&value.birth!==undefined)return {id:value.id,vertices:value.vertices,edges:value.edges.map(e=>e.id),birth:value.birth};
  return Object.fromEntries(Object.entries(value).filter(([k])=>!['nodes','edges'].includes(k)).map(([k,v])=>[k,clean(v)]));
 }
 return value;
}
const faces=T.detectFaces(g.nodes,g.edges,800),independent=T.independentFaces(g.edges,faces);
const options={relations:new Map([['link',.6]]),anchors:new Map([['node',Model.sphere(0,1,250)]]),extra:.46,anchor:.38,repulsion:.54,collision:.72};
const physics=Model.enrich(JSON.parse(JSON.stringify(input.graph)));
for(let i=0;i<4;i++)Model.forceStep(physics,options);
const app=fs.readFileSync(require('node:path').join(__dirname,'../reference/csv-importer/src/app.js'),'utf8');
const prepare=app.slice(app.indexOf('function prepareWeights()'),app.indexOf('function buildAnchors()'));
const weights={};
for(const mode of ['strength','distance']){
 const context={graph:{edges:input.graph.edges.map(e=>({...e}))},state:{weightMode:mode},number:(v,d)=>Number.isFinite(Number(v))?Number(v):d};
 require('node:vm').runInNewContext(prepare+'; prepareWeights();',context);
 weights[mode]=context.graph.edges.map(e=>({filterWeight:e.filterWeight,forceWeight:e.forceWeight}));
}
process.stdout.write(JSON.stringify({
 components:Model.components(g),weights,
 physics:physics.nodes.map(n=>Object.fromEntries(['id','x','y','z','vx','vy','vz'].map(k=>[k,n[k]]))),
 filtration:clean(T.runFiltration(g.nodes,g.edges,input.epsilon)),faces:faces.map(clean),independent:independent.map(clean),
 persistence:T.persistentHomology(g.nodes,g.edges,independent),analysis:clean(T.analyze(g.nodes,g.edges,input.epsilon,input.fill)),
 metrics:g.nodes.map(n=>({id:n.id,depth:n.depth,degree:n.degree,rank:n.rank,metrics:n.metrics,descendantCount:n.descendantCount,ancestorCount:n.ancestorCount})),
 layouts:Object.fromEntries(['semantic','hierarchical','cluster','radial'].map(name=>[name,clean(name==='radial'?Model.radialTargets(g,g.nodes[0]?.id):name==='hierarchical'?Model.hierarchicalTargets(g.nodes):Model[name+'Targets'](g.nodes,'category'))]))
}));
