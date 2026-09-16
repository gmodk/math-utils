"""CSV model port and explicit fork compatibility projections."""
import math
from collections import deque

def sphere(i,total,radius,center=None):
    c = center or dict(x=0,y=0,z=0)
    y = 1-2*(i+.5)/max(1,total); r = math.sqrt(max(0,1-y*y)); a = math.pi*(3-math.sqrt(5))*i
    return dict(x=c['x']+math.cos(a)*r*radius,y=c['y']+y*radius,z=c['z']+math.sin(a)*r*radius)

def traverse(start, node_map, key, limit=None):
    seen = set(); ordered = []; queue = deque([(start,0)])
    while queue:
        id,depth = queue.popleft()
        if id in seen: continue
        seen.add(id); ordered.append(id)
        if limit is None or depth < limit:
            queue.extend((v,depth+1) for v in node_map.get(id,{}).get(key,[]) if v not in seen)
    return ordered

def display_schema(nodes,edges):
    columns = dict.fromkeys(k for n in nodes for k in n.get('properties',{})); categorical=[]; numeric=[]
    for col in columns:
        values = [str(n.get('properties',{}).get(col,'')) for n in nodes if str(n.get('properties',{}).get(col,'')).strip()]
        if not values: continue
        nums=[]
        for v in values:
            try:
                n=float(v)
                if math.isfinite(n): nums.append(n)
            except ValueError: pass
        if len(nums)/len(values)>=.8: numeric.append(dict(key=col,min=min(nums),max=max(nums)))
        else:
            unique=sorted(set(values)); limit=min(64,max(4,math.floor(math.sqrt(len(nodes))*2+.5)))
            if 2<=len(unique)<=limit and len(unique)<=len(nodes)*.7: categorical.append(dict(key=col,values=unique))
    if not any(c['key']=='category' for c in categorical):
        categories=sorted({n.get('category','node') for n in nodes})
        if categories: categorical.insert(0,dict(key='category',values=categories,virtual=True))
    return dict(categorical=categorical,numeric=numeric,edgeTypes=sorted({e.get('relation') or e.get('type') or 'unspecified' for e in edges}))

def enrich(graph, include_reachability=True):
    nodes=graph['nodes']; node_map={n['id']:n for n in nodes}; edges=graph['edges']; count=max(1,len(nodes))
    # `type` is presentation-only. Canonical/exported records use nullable `relation`.
    for e in edges:e['type']=e.get('relation') or e.get('type') or 'unspecified'
    for i,n in enumerate(nodes):
        p=sphere(i,len(nodes),max(210,math.sqrt(len(nodes))*42))
        n.update(p); n.update(homeX=p['x'],homeY=p['y'],homeZ=p['z'],vx=0,vy=0,vz=0,toIds=[],fromIds=[],neighborIds=[],depth=0)
    for e in edges:
        a=node_map[e['source']]; b=node_map[e['target']]
        a['neighborIds'].append(b['id']); b['neighborIds'].append(a['id']); a['toIds'].append(b['id']); b['fromIds'].append(a['id'])
        if not e.get('directed'):
            b['toIds'].append(a['id']); a['fromIds'].append(b['id'])
    for n in nodes:
        for key in ('toIds','fromIds','neighborIds'): n[key]=list(dict.fromkeys(n[key]))
    depths={n['id']:0 for n in nodes if not n['fromIds']}; queue=deque(depths)
    while queue:
        id=queue.popleft()
        for target in node_map[id]['toIds']:
            d=min(8,depths[id]+1)
            if target not in depths or depths[target]>d: depths[target]=d;queue.append(target)
    rank={n['id']:1/count for n in nodes}
    for _ in range(24):
        nxt={n['id']:.15/count for n in nodes}; dangling=0
        for n in nodes:
            if not n['toIds']: dangling+=rank[n['id']]
            else:
                for id in n['toIds']: nxt[id]+=.85*rank[n['id']]/len(n['toIds'])
        rank={id:v+.85*dangling/count for id,v in nxt.items()}
    denom=max(1,len(nodes)-1)
    for n in nodes:
        n['depth']=depths.get(n['id'],2 if n['fromIds'] else 0)
        down=traverse(n['id'],node_map,'toIds'); up=traverse(n['id'],node_map,'fromIds')
        nd=len(down)-1; nu=len(up)-1; degree=len(n['neighborIds'])
        n.update(degree=degree,rank=rank[n['id']],descendantCount=nd,ancestorCount=nu,
                 metrics=dict(degree=degree/denom,pagerank=rank[n['id']],reachability=(nd+nu)/(2*denom),descendants=nd/denom,prerequisites=nu/denom))
        if include_reachability: n.update(upstream=up,downstream=down)
    ranges={key:[min((n['metrics'][key] for n in nodes),default=0),max((n['metrics'][key] for n in nodes),default=0)] for key in ('degree','pagerank','reachability','descendants','prerequisites')}
    return dict(nodes=nodes,edges=edges,metricRanges=ranges,schema=display_schema(nodes,edges))

def targets(graph,layout,key='category',center_id=None):
    nodes=graph['nodes']; groups={}; out={}
    if layout in ('force','home'): return {n['id']:dict(x=n['homeX'],y=n['homeY'],z=n['homeZ']) for n in nodes}
    if layout=='radial':
        distances={center_id:0}; queue=deque([center_id]); node_map={n['id']:n for n in nodes}
        while queue:
            id=queue.popleft()
            for v in node_map.get(id,{}).get('neighborIds',[]):
                if v not in distances: distances[v]=distances[id]+1;queue.append(v)
        for n in nodes: groups.setdefault(distances.get(n['id'],99),[]).append(n)
        out[center_id]=dict(x=0,y=0,z=0)
        for d,ls in groups.items():
            if not d: continue
            r=680 if d==99 else min(580,d*110)
            for i,n in enumerate(sorted(ls,key=lambda n:n['label'])): out[n['id']]=sphere(i,len(ls),r)
        return out
    for n in nodes:
        value=n['depth'] if layout=='hierarchical' else (n.get('category') if key=='category' else n.get('properties',{}).get(key)) or 'unassigned'
        groups.setdefault(value,[]).append(n)
    for i,(value,ls) in enumerate(sorted(groups.items())):
        if layout=='hierarchical':
            ls=sorted(ls,key=lambda n:(n['category'],n['label'])); radius=max(90,len(ls)*5.4); y=(i-(len(groups)-1)/2)*150
            for j,n in enumerate(ls): out[n['id']]=dict(x=math.cos(j/len(ls)*math.tau)*radius,y=y,z=math.sin(j/len(ls)*math.tau)*radius)
        else:
            if layout=='semantic':
                a=i/max(1,len(groups))*math.tau;c=dict(x=math.cos(a)*380,y=(i%3-1)*90,z=math.sin(a)*380);ls=sorted(ls,key=lambda n:-n['rank']);r=max(48,math.sqrt(len(ls))*31)
            else: c=sphere(i,len(groups),max(260,len(groups)*36));ls=sorted(ls,key=lambda n:n['label']);r=max(42,math.sqrt(len(ls))*28)
            for j,n in enumerate(ls): out[n['id']]=sphere(j,len(ls),r,c)
    return out

def force_step(nodes,edges,options,steps=1):
    node_map={n['id']:n for n in nodes}; repulsion=800+3100*options.get('repulsion',.54); damping=.84+.1*(1-options.get('repulsion',.54)); collision=10+24*options.get('collision',.72)
    for _ in range(min(12,max(1,steps))):
        if len(nodes)<=460:
            for i,a in enumerate(nodes):
                for b in nodes[i+1:]:
                    delta=[a[k]-b[k] for k in 'xyz'];d2=sum(v*v for v in delta)+12;d=math.sqrt(d2);f=repulsion/d2+((collision-d)*.05 if d<collision else 0)
                    for k,v in zip('xyz',delta): a['v'+k]+=v/d*f;b['v'+k]-=v/d*f
        for e in edges:
            a=node_map[e['source']];b=node_map[e['target']];delta=[b[k]-a[k] for k in 'xyz'];d=math.sqrt(sum(v*v for v in delta)) or 1
            relation=options.get('relations',{}).get(e.get('relation') or e.get('type') or 'unspecified',options.get('extra',.46)); strength=.0008+relation*.0042;desired=88+(1-relation)*80
            weight=e.get('forceWeight')
            if weight is None: weight=e.get('weight')
            if weight is None: weight=1
            f=(d-desired)*strength*(.5+.5*max(.1,weight))
            for k,v in zip('xyz',delta): a['v'+k]+=v/d*f;b['v'+k]-=v/d*f
        for n in nodes:
            anchor=options.get('anchors',{}).get(n.get('category') or 'node')
            for k in 'xyz':
                if anchor: n['v'+k]+=(anchor[k]-n[k])*options.get('anchor',.38)*.00065
                n['v'+k]*=damping;n[k]+=n['v'+k]
    return nodes

def components(nodes,edges):
    """Original Model.components helper; callers supply their filtered edges."""
    parent={n['id']:n['id'] for n in nodes}
    def find(id):
        while parent[id]!=id:id=parent[id]
        return id
    for e in edges:
        a,b=find(e['source']),find(e['target'])
        if a!=b:parent[b]=a
    groups=list(dict.fromkeys(find(n['id']) for n in nodes))
    return dict(groups=groups,beta0=len(groups),beta1=max(0,len(edges)-len(nodes)+len(groups)),edges=len(edges))
