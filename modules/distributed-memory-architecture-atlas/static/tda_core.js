/* Pure client-side TDA helpers for the Graph / TDA Lab.
 * Builds the simplicial lift of hyperedge supports and computes Betti numbers
 * over F2 from boundary-matrix ranks. No backend state is modified.
 */
(function(root){
  'use strict';
  function combos(arr,k){const out=[];function rec(start,acc){if(acc.length===k){out.push([...acc]);return;}for(let i=start;i<=arr.length-(k-acc.length);i++){acc.push(arr[i]);rec(i+1,acc);acc.pop();}}rec(0,[]);return out;}
  const key=v=>v.join('-');
  function minBirth(map,vertices,birth){const k=key(vertices),prev=map.get(k);if(!prev||birth<prev.birth)map.set(k,{key:k,vertices:[...vertices],birth});}
  function buildComplex(supports,maxDim=3){
    const edges=new Map(),triangles=new Map(),tetras=new Map();
    for(const s of supports){
      for(const v of combos(s.vertices,2))minBirth(edges,v,s.birth);
      if(maxDim>=2)for(const v of combos(s.vertices,3))minBirth(triangles,v,s.birth);
      if(maxDim>=3)for(const v of combos(s.vertices,4))minBirth(tetras,v,s.birth);
    }
    return {supports:[...supports],edges:[...edges.values()],triangles:[...triangles.values()],tetras:[...tetras.values()]};
  }
  const bit=i=>1n<<BigInt(i);
  function rankBitColumns(cols){const basis=new Map();let rank=0;for(let x of cols){while(x){const pivot=x.toString(2).length-1;if(basis.has(pivot))x^=basis.get(pivot);else{basis.set(pivot,x);rank++;break;}}}return rank;}
  function componentsFromEdges(n,edges){const parent=Array.from({length:n},(_,i)=>i);const find=a=>parent[a]===a?a:(parent[a]=find(parent[a]));const union=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent[b]=a;};edges.forEach(e=>union(e.vertices[0],e.vertices[1]));const remap=new Map();let c=0;return Array.from({length:n},(_,i)=>{const r=find(i);if(!remap.has(r))remap.set(r,c++);return remap.get(r);});}
  function cycleEdgeSet(n,edges){const parent=Array.from({length:n},(_,i)=>i);const find=a=>parent[a]===a?a:(parent[a]=find(parent[a]));const out=new Set();for(const e of edges){let a=find(e.vertices[0]),b=find(e.vertices[1]);if(a===b)out.add(e.key);else parent[b]=a;}return out;}
  function topologyAt(complex,n,t,maxDim=3){
    const es=complex.edges.filter(s=>s.birth<=t+1e-12),ts=maxDim>=2?complex.triangles.filter(s=>s.birth<=t+1e-12):[],qs=maxDim>=3?complex.tetras.filter(s=>s.birth<=t+1e-12):[];
    const eIndex=new Map(es.map((e,i)=>[e.key,i])),tIndex=new Map(ts.map((s,i)=>[s.key,i]));
    const b1=es.map(e=>bit(e.vertices[0])|bit(e.vertices[1]));
    const b2=ts.map(tr=>{let v=0n;for(const face of combos(tr.vertices,2)){const i=eIndex.get(key(face));if(i!==undefined)v|=bit(i);}return v;});
    const b3=qs.map(q=>{let v=0n;for(const face of combos(q.vertices,3)){const i=tIndex.get(key(face));if(i!==undefined)v|=bit(i);}return v;});
    const r1=rankBitColumns(b1),r2=rankBitColumns(b2),r3=rankBitColumns(b3);
    return {beta0:n-r1,beta1:es.length-r1-r2,beta2:ts.length-r2-r3,beta3:qs.length-r3,edges:es,triangles:ts,tetras:qs,components:componentsFromEdges(n,es),cycleKeys:cycleEdgeSet(n,es),ranks:{b1:r1,b2:r2,b3:r3}};
  }
  function samples(complex,n,maxDim=3,count=24){const out=[];for(let i=0;i<=count;i++){const t=i/count;out.push({t,...topologyAt(complex,n,t,maxDim)});}return out;}
  root.AtlasTDA={combos,buildComplex,topologyAt,samples,rankBitColumns,componentsFromEdges,cycleEdgeSet};
})(typeof window!=='undefined'?window:globalThis);
