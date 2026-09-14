from __future__ import annotations
from itertools import combinations
from ..core.combinatorics import cover_regions, capacity
from ..core.finite_field import rank

ID="sheaf";NAME="Sheaf / Local-to-global"

def _simplices(regions,max_dim):
    rs=[set(s) for s in regions];levels=[]
    for d in range(max_dim+1):
        lvl=[]
        for ids in combinations(range(len(regions)),d+1):
            inter=set(rs[ids[0]])
            for j in ids[1:]:inter&=rs[j]
            if inter:lvl.append((ids,tuple(sorted(inter))))
        levels.append(lvl)
    return levels

def _offsets(level,model):
    o={};t=0
    for ids,sup in level:o[ids]=t;t+=len(sup) if model=="coordinate" else 1
    return o,t

def _delta(a,b,model,p):
    so,sd=_offsets(a,model);to,td=_offsets(b,model)
    if td==0:return []
    m=[[0]*sd for _ in range(td)];by={ids:(ids,sup) for ids,sup in a}
    for ids,sup in b:
        bo=to[ids]
        for j in range(len(ids)):
            face=ids[:j]+ids[j+1:]
            if face not in by:continue
            _,fs=by[face];sgn=1 if j%2==0 else -1;fo=so[face]
            if model=="spectral_line":m[bo][fo]=(m[bo][fo]+sgn)%p
            else:
                pos={v:i for i,v in enumerate(fs)}
                for oi,v in enumerate(sup):m[bo+oi][fo+pos[v]]=(m[bo+oi][fo+pos[v]]+sgn)%p
    return m

def _cohomology(regions,p,max_dim,model):
    levels=_simplices(regions,max_dim);dims=[_offsets(l,model)[1] for l in levels];ranks=[]
    for k in range(max_dim):
        d=_delta(levels[k],levels[k+1],model,p);ranks.append(rank(d,p) if d else 0)
    betti=[]
    for k,d in enumerate(dims):betti.append(d-(ranks[k] if k<len(ranks) else 0)-(ranks[k-1] if k>0 else 0))
    return {"cochain_dimensions":dims,"coboundary_ranks":ranks,"cohomology_dimensions":betti,"simplex_counts":[len(l) for l in levels]}

def _compatibility(regions,sections,p):
    bad=[];comparisons=0
    for i,j in combinations(range(len(regions)),2):
        common=sorted(set(regions[i])&set(regions[j]));pi={v:k for k,v in enumerate(regions[i])};pj={v:k for k,v in enumerate(regions[j])};coords=[]
        for v in common:
            comparisons+=1
            if sections[i][pi[v]]%p!=sections[j][pj[v]]%p:coords.append(v+1)
        if coords:bad.append({"region_a":i+1,"region_b":j+1,"coordinates":coords})
    return {"compatible":not bad,"comparisons":comparisons,"mismatch_count":len(bad),"mismatches":bad[:30]}

def analyze(exp, *, model="coordinate"):
    regs=cover_regions(exp.n,exp.mode,exp.region_limit)
    sections=[[exp.field_projection[i]%exp.p for i in s] for s in regs]
    coh=_cohomology(regs,exp.p,min(3,exp.max_dim),model)
    return {"approach":ID,"name":NAME,"summary":{"model":model,"declared_capacity":capacity(exp.mode,exp.n),"cover_regions":len(regs),"max_dim":exp.max_dim},
            "cohomology":coh,"compatibility":_compatibility(regs,sections,exp.p),
            "regions":[[i+1 for i in r] for r in regs],"sections":sections,
            "interpretation":"Regions are patches of a cover, their overlaps define the nerve, and local coordinate sections glue to a global state precisely when the restriction data are compatible. H^0 measures global sections; higher cohomology measures obstruction structure."}
