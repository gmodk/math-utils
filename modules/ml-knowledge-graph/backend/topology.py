"""Port of supplied CSVGraphTopology: graph/cellular persistence over F_2.

No simplicial completion, cohomology, or circular coordinates are performed.
"""
def endpoints(e):
    return e.get('source', e.get('a', {}).get('id')), e.get('target', e.get('b', {}).get('id'))

def run_filtration(nodes, edges, epsilon):
    parent = {n['id']: n['id'] for n in nodes}; sizes = dict.fromkeys(parent, 1)
    def find(x):
        r = x
        while parent[r] != r: r = parent[r]
        while parent[x] != x:
            nxt = parent[x]; parent[x] = r; x = nxt
        return r
    merges = []; cycles = []; count = 0
    for e in edges:
        if e['filterWeight'] > epsilon: continue
        count += 1; a, b = map(find, endpoints(e))
        if a != b:
            if sizes[a] < sizes[b]: a, b = b, a
            parent[b] = a; sizes[a] += sizes[b]; merges.append(e['id'])
        else: cycles.append(e['id'])
    roots = {n['id']: find(n['id']) for n in nodes}; counts = {}
    for r in roots.values(): counts[r] = counts.get(r, 0)+1
    return dict(components=len(counts), beta1=len(cycles), edgeCount=count, mergeEdgeIds=merges, cycleEdgeIds=cycles, rootByNode=roots, componentSizes=counts)

def detect_faces(nodes, edges, max_faces=800):
    by_pair = {}; neighbors = {n['id']: set() for n in nodes}
    for e in edges:
        a,b = endpoints(e); key = tuple(sorted((a,b)))
        if key not in by_pair or by_pair[key]['filterWeight'] > e['filterWeight']: by_pair[key] = e
        neighbors[a].add(b); neighbors[b].add(a)
    ids = sorted(neighbors); faces = []; seen = set()
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            shared = sorted(neighbors[a] & neighbors[b])
            for x,c in enumerate(shared):
                for d in shared[x+1:]:
                    if len(faces) >= max_faces: return faces
                    vertices = [a,c,b,d]; signature = '|'.join(sorted(vertices))
                    if signature in seen: continue
                    seen.add(signature)
                    boundary = [by_pair[tuple(sorted(pair))] for pair in [(a,c),(c,b),(b,d),(d,a)]]
                    faces.append(dict(id='f:'+signature, vertices=vertices, edges=boundary, birth=max(e['filterWeight'] for e in boundary)))
    return faces

def independent_faces(edges, faces):
    index = {e['id']: i for i,e in enumerate(edges)}; basis = {}; chosen = []
    for face in sorted(faces, key=lambda f:(f['birth'], f['id'])):
        boundary = 0
        for e in face['edges']: boundary ^= 1 << index[e['id']]
        while boundary and boundary.bit_length()-1 in basis: boundary ^= basis[boundary.bit_length()-1]
        if boundary:
            basis[boundary.bit_length()-1] = boundary; chosen.append(face)
    return chosen

def persistent_homology(nodes, edges, faces):
    cells = [dict(key='v:'+n['id'], dim=0, weight=0, boundary=[]) for n in nodes]
    cells += [dict(key='e:'+e['id'], dim=1, weight=e['filterWeight'], boundary=['v:'+v for v in endpoints(e)]) for e in edges]
    cells += [dict(key='f:'+f['id'], dim=2, weight=f['birth'], boundary=['e:'+e['id'] for e in f['edges']]) for f in faces]
    cells.sort(key=lambda c:(c['weight'], c['dim'], c['key']))
    index = {c['key']: i for i,c in enumerate(cells)}; reduced = []; owners = {}; births = []; pairs = {}
    for j,cell in enumerate(cells):
        column = 0
        for key in cell['boundary']:
            if key in index: column ^= 1 << index[key]
        while column and column.bit_length()-1 in owners: column ^= reduced[owners[column.bit_length()-1]]
        reduced.append(column)
        if not column: births.append(j)
        else:
            pivot = column.bit_length()-1; owners[pivot] = j; pairs[pivot] = j
    result = []
    for i in births:
        birth = cells[i]['weight']; death = cells[pairs[i]]['weight'] if i in pairs else None
        if death is None or death > birth + 1e-12: result.append(dict(dim=cells[i]['dim'], birth=birth, death=death))
    return result

def analyze(nodes, edges, epsilon=.52, fill_areas=False):
    edges = sorted(edges, key=lambda e:(e['filterWeight'],e['id']))
    candidates = detect_faces(nodes, edges) if fill_areas else []
    faces = independent_faces(edges, candidates) if fill_areas else []
    intervals = persistent_homology(nodes,edges,faces); current = run_filtration(nodes,edges,epsilon)
    active = [f for f in faces if f['birth'] <= epsilon]
    def betti(dim, eps): return sum(x['dim']==dim and x['birth']<=eps and (x['death'] is None or x['death']>eps) for x in intervals)
    colors = ['#72e5ff','#ff8fd8','#a4ef9b','#ffd36e','#ad9cff','#72a8ff','#ff9c72','#7cf0cf']
    root_index = {r:i for i,r in enumerate(sorted(current['componentSizes']))}
    result = dict(current=current,candidates=candidates,faces=faces,activeFaces=active,intervals=intervals,
        curves=[dict(epsilon=i/40, **{f'beta{d}':betti(d,i/40) for d in range(3)}) for i in range(41)],
        euler=len(nodes)-current['edgeCount']+len(active),largest=max(current['componentSizes'].values(),default=0),
        componentColorByNode={n:colors[root_index[r]%8] for n,r in current['rootByNode'].items()},
        componentIndexByNode={n:root_index[r]+1 for n,r in current['rootByNode'].items()})
    for d in range(3):
        result[f'beta{d}'] = betti(d,epsilon)
        result[f'h{d}'] = [[x['birth'], 1 if x['death'] is None else x['death']] for x in intervals if x['dim']==d]
    return result

def weights(edges, field='weight', mode='strength'):
    """Return derived filtration values without changing source measurements."""
    values = [float(e[field]) if e.get(field) is not None else 1.0 for e in edges]
    lo = min(values, default=0); span = max(values, default=0)-lo
    for e,v in zip(edges,values):
        n = (v-lo)/span if span else .5
        e['filterWeight'] = 1-n if mode=='strength' else n
        e['forceWeight'] = n if mode=='strength' else 1-n
    return edges
