"""Preserve the fork's graph projection and layout parameters in Python."""
import math
import random
from collections import deque
from .graph_analysis import traverse

def project(raw):
    # Bundled graphs retain their precomputed (pre-transitive-reduction) metrics.
    if isinstance(raw,list):
        nodes=[dict(n) for n in raw]; edges=[dict(source=n['id'],target=id,directed=True) for n in nodes for id in n.get('to',[])]
    else:
        nodes=[dict(n) for n in raw['nodes']];edges=[dict(e) for e in raw['edges']]
        for e in edges:e['type']=e.get('relation') or e.get('type') or 'unspecified'
        by_id={n['id']:n for n in nodes}
        for n in nodes: n.update(to=[],**{'from':[]})
        for e in edges:
            by_id[e['source']]['to'].append(e['target']);by_id[e['target']]['from'].append(e['source'])
            if not e.get('directed'):
                by_id[e['target']]['to'].append(e['source']);by_id[e['source']]['from'].append(e['target'])
        for n in nodes:n['csvRelations']=[e for e in edges if n['id'] in (e['source'],e['target'])]
    node_map={n['id']:n for n in nodes}; computing=set(); done=set()
    for n in nodes:
        n.update(category=n.get('category') or '',definition=n.get('definition') or n.get('description') or '',long_description=n.get('long_description') or '',x=0,y=0,z=0)
        for k in ('to','from'): n[k]=list(dict.fromkeys(v for v in n.get(k,[]) if v in node_map))
    def depth(id):
        n=node_map[id]
        if id in done:return n['depth']
        if id in computing:return 0
        computing.add(id);n['depth']=1+max((depth(v) for v in n['from']),default=-1);computing.remove(id);done.add(id);return n['depth']
    for n in nodes:
        depth(n['id']);down=traverse(n['id'],node_map,'to');up=traverse(n['id'],node_map,'from')
        n.update(upstream=up,downstream=down,descendantCount=len(down)-1,ancestorCount=len(up)-1)
        r=max(1.5,min(6,2*math.log2(len(down))))
        n.update(radius=r,_baseScale=r,_currentScale=r)
    if not isinstance(raw,list):
        # New CSV metrics use the supplied importer definitions, clearly namespaced.
        from .graph_analysis import enrich
        model=enrich({'nodes':[dict(n) for n in raw['nodes']],'edges':edges},False)
        for n,m in zip(nodes,model['nodes']):
            n.update(_pagerank=m['rank'],_degree_centrality=m['metrics']['degree'],_reachability_ratio=m['metrics']['reachability'],_descendant_ratio=m['metrics']['descendants'],_prerequisite_ratio=m['metrics']['prerequisites'])
    return dict(nodes=nodes,edges=edges)

def point(i,count,r,c=None):
    c=c or dict(x=0,y=0,z=0);phi=math.acos(1-2*(i+.5)/count);theta=math.pi*(1+math.sqrt(5))*i
    return dict(x=c['x']+r*math.sin(phi)*math.cos(theta),y=c['y']+r*math.sin(phi)*math.sin(theta),z=c['z']+r*math.cos(phi))

def layout(nodes,edges,name,center=None,seed=42):
    rng=random.Random(seed); groups={};out={};node_map={n['id']:n for n in nodes}
    if name=='hierarchical':
        for n in nodes:groups.setdefault(n['depth'],[]).append(n)
        max_depth=max(groups,default=0)
        for d,ls in groups.items():
            ls=sorted(ls,key=lambda n:n['category']);r=max(20,len(ls)*3)
            for i,n in enumerate(ls):out[n['id']]=dict(x=math.cos(i/len(ls)*math.tau)*r+(rng.random()-.5)*6,y=(d-max_depth/2)*40,z=math.sin(i/len(ls)*math.tau)*r+(rng.random()-.5)*6)
    elif name=='cluster':
        for n in nodes:groups.setdefault(n['category'] or 'other',[]).append(n)
        for i,ls in enumerate(groups.values()):
            c=point(i,len(groups),300)
            for j,n in enumerate(ls):out[n['id']]=point(j,len(ls),max(20,math.sqrt(len(ls))*8),c)
    elif name=='radial':
        distances={center:0};q=deque([center]);out[center]=dict(x=0,y=0,z=0)
        while q:
            id=q.popleft()
            for v in node_map[id]['from']+node_map[id]['to']:
                if v not in distances:distances[v]=distances[id]+1;q.append(v)
        for id,d in distances.items():
            if d:groups.setdefault(d,[]).append(id)
        for d,ls in groups.items():
            for i,id in enumerate(ls):out[id]=point(i,len(ls),d*40 if d<=5 else 200+(d-5)*10)
        for n in nodes:
            if n['id'] not in out:
                phi=rng.random()*math.pi;theta=rng.random()*math.tau
                out[n['id']]=dict(x=250*math.sin(phi)*math.cos(theta),y=250*math.sin(phi)*math.sin(theta),z=250*math.cos(phi))
    else:
        # D3 force configuration port: link, charge, center, axis, cluster.
        # Exact pairwise charge replaces the source Barnes-Hut approximation.
        import numpy as np
        count=len(nodes)
        if not count:return {}
        p=np.array([[(rng.random()-.5)*100 for _ in range(3)] for n in nodes]);v=np.zeros_like(p)
        indexes={n['id']:i for i,n in enumerate(nodes)};links=np.array([(indexes[e['source']],indexes[e['target']]) for e in edges if e['source'] in indexes and e['target'] in indexes],dtype=int).reshape(-1,2)
        degree=np.bincount(links.ravel(),minlength=count) if len(links) else np.zeros(count)
        for i,n in enumerate(nodes):groups.setdefault(n['category'],[]).append(i)
        alpha=1.
        for tick in range(max(120,min(220,round(110+math.sqrt(count)*2)))):
            alpha*=.965
            if len(links):
                a,b=links[:,0],links[:,1];delta=(p[b]+v[b])-(p[a]+v[a]);length=np.linalg.norm(delta,axis=1);length=np.maximum(length,1e-6)
                force=delta*((length-30)/length*alpha*.3)[:,None];bias=degree[a]/np.maximum(1,degree[a]+degree[b]);np.add.at(v,b,-force*bias[:,None]);np.add.at(v,a,force*(1-bias)[:,None])
            for start in range(0,count,128):
                delta=p[start:start+128,None,:]-p[None,:,:];sq=np.sum(delta*delta,axis=2);mask=(sq>0)&(sq<90000);den=np.where(sq<1,np.sqrt(np.maximum(sq,1e-12)),sq)
                v[start:start+128]+=np.sum(delta*np.where(mask,80*alpha/np.maximum(den,1e-12),0)[:,:,None],axis=1)
            p-=p.mean(axis=0);v-=p*.02*alpha
            for ids in groups.values():v[ids]+=(p[ids].mean(axis=0)-p[ids])*.15*alpha
            v*=.6;p+=v
            if alpha<.018:break
        out={n['id']:dict(zip('xyz',map(float,p[i]))) for i,n in enumerate(nodes)}
    return out
