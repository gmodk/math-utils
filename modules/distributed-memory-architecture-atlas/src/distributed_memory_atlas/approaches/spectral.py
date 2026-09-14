from __future__ import annotations
from itertools import combinations
from ..core.combinatorics import region_subsets, normalize_layers
from ..core.finite_field import rank, inv, identity, outer, matsub
from ..core.polynomial import residues

ID="spectral"; NAME="Spectral Hypergraph"

def _constraint_rows(local, subset, n, p):
    v=[int(x)%p for x in local]
    pivot=next((i for i,x in enumerate(v) if x),None)
    if pivot is None:return []
    dual=[0]*len(v);dual[pivot]=inv(v[pivot],p)
    a=outer(v,dual,p); h=matsub(a,identity(len(v)),p)
    out=[]
    for lr in h:
        row=[0]*n
        for j,g in enumerate(subset): row[g]=lr[j]%p
        out.append(row)
    return out

def _boundary_rank(simplices_k, simplices_km1):
    if not simplices_k or not simplices_km1:return 0
    idx={s:i for i,s in enumerate(simplices_km1)}
    mat=[[0]*len(simplices_k) for _ in simplices_km1]
    for j,s in enumerate(simplices_k):
        for face in combinations(s,len(s)-1):
            i=idx.get(tuple(face))
            if i is not None: mat[i][j]^=1
    return rank(mat,2)

def _tda(active_subsets, max_dim=2):
    faces=[set() for _ in range(max_dim+2)]
    for s in active_subsets:
        for k in range(1,min(len(s),max_dim+2)+1):
            for f in combinations(s,k):faces[k-1].add(tuple(f))
    levels=[sorted(x) for x in faces]
    boundary=[0]
    for k in range(1,len(levels)): boundary.append(_boundary_rank(levels[k],levels[k-1]))
    betti=[]
    for k in range(max_dim+1):
        betti.append(len(levels[k])-boundary[k]-(boundary[k+1] if k+1<len(boundary) else 0))
    return {"simplex_counts":[len(levels[k]) for k in range(max_dim+1)],"betti":betti}

def analyze(exp, *, preview_limit=120):
    n,p=exp.n,exp.p
    if p<=n: raise ValueError("spectral analysis requires prime p > n for the default CRT evaluation points")
    coeff=[int(x)%p for x in exp.field_projection]
    points=list(range(1,n+1)); y=residues(coeff,points,p)
    raw=[]
    for rid,s in enumerate(region_subsets(n,exp.mode),1):
        if len(s)==0:
            raw.append({"id":rid,"kind":"anchor","subset":s,"rows":[],"active":True})
        elif len(s)==1:
            raw.append({"id":rid,"kind":"share","subset":s,"rows":[],"active":exp.spectral_policy=="full"})
        else:
            rows=_constraint_rows([y[i] for i in s],s,n,p)
            raw.append({"id":rid,"kind":"spectral","subset":s,"rows":rows,"active":exp.spectral_policy=="full"})
    if not any(r["kind"]=="anchor" for r in raw):
        raise ValueError("spectral M/Q/R analysis requires grade 0 anchor")
    if exp.spectral_policy=="rank-basis":
        selected={r["id"] for r in raw if r["kind"]=="anchor"}; current=[]; rr=0; target=max(0,n-1)
        candidates=[r for r in raw if r["kind"]=="spectral" and r["rows"]]
        while rr<target:
            best=None; best_rank=rr
            for r in candidates:
                trial=current+r["rows"]; tr=rank(trial,p)
                if tr>best_rank or (tr==best_rank and tr>rr and best and (len(r["subset"]),r["id"])<(len(best["subset"]),best["id"])):
                    best,best_rank=r,tr
            if best is None:break
            selected.add(best["id"]);current+=best["rows"];rr=rank(current,p);candidates.remove(best)
        for r in raw:r["active"]=r["id"] in selected
    active=[r for r in raw if r["active"]]
    rows=[row for r in active for row in r["rows"]]
    rr=rank(rows,p)
    subsets=[r["subset"] for r in active if len(r["subset"])>0]
    tda=_tda(subsets,max_dim=min(2,exp.max_dim))
    return {
        "approach":ID,"name":NAME,
        "summary":{"n":n,"p":p,"mode":exp.mode,"layers":list(normalize_layers(exp.mode)),"policy":exp.spectral_policy,
                   "abstract_regions":len(raw),"physical_regions":len(active),"constraint_rank":rr,"target_rank":max(0,n-1),
                   "projectively_recoverable":rr>=max(0,n-1),"compression_ratio":len(active)/len(raw) if raw else 0},
        "polynomial":{"coefficients":coeff,"evaluation_points":points,"crt_values":y},
        "tda":tda,
        "regions":[{"id":r["id"],"kind":r["kind"],"subset":[i+1 for i in r["subset"]],"row_count":len(r["rows"]),"active":r["active"]} for r in raw[:preview_limit]],
        "region_preview_truncated":len(raw)>preview_limit,
        "_active_blocks":[{"id":r["id"],"kind":r["kind"],"rows":r["rows"]} for r in active],
        "interpretation":"The finite-field projection is treated as polynomial coefficients; CRT evaluations are constrained locally by region eigenspaces. The token is determined projectively when the stacked local constraints have rank n-1, then the anchor fixes scale."
    }
