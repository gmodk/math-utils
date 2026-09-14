from __future__ import annotations
import random, math
from collections import Counter
from statistics import mean
from ..core.finite_field import rank
from .combinatorial import systematic_matrix
from . import spectral

ID="probabilistic"; NAME="Probabilistic"

def _wilson(successes,trials,z=1.959963984540054):
    if not trials:return [0,0]
    ph=successes/trials; den=1+z*z/trials
    center=(ph+z*z/(2*trials))/den
    half=z*math.sqrt(ph*(1-ph)/trials+z*z/(4*trials*trials))/den
    return [max(0,center-half),min(1,center+half)]

def _simulate_systematic(exp,q,trials,seed):
    matrix,_=systematic_matrix(exp.n,exp.mode)
    rng=random.Random(seed); succ=0;ranks=[]
    for _ in range(trials):
        rows=[row for row in matrix if rng.random()<q]
        r=rank(rows,exp.p) if rows else 0;ranks.append(r);succ+=r>=exp.n
    return {"recovery_probability":succ/trials,"wilson95":_wilson(succ,trials),"expected_rank":mean(ranks),"rank_histogram":dict(sorted(Counter(ranks).items()))}

def _simulate_spectral(exp,q,trials,seed):
    spec=spectral.analyze(exp)
    blocks=spec["_active_blocks"]
    rng=random.Random(seed); succ=0;ranks=[]
    for _ in range(trials):
        kept=[];anchor=False
        for b in blocks:
            if rng.random()<q:
                kept+=b["rows"]
                if b["kind"]=="anchor":anchor=True
        r=rank(kept,exp.p) if kept else 0;ranks.append(r)
        succ+=anchor and r>=max(0,exp.n-1)
    return {"recovery_probability":succ/trials,"wilson95":_wilson(succ,trials),"expected_rank":mean(ranks),"rank_histogram":dict(sorted(Counter(ranks).items())),"physical_regions":len(blocks)}

def _stopping_systematic(exp,trials,seed):
    matrix,_=systematic_matrix(exp.n,exp.mode);N=len(matrix);rng=random.Random(seed);times=[]
    for _ in range(trials):
        order=list(range(N));rng.shuffle(order);rows=[];t=N+1
        for k,i in enumerate(order,1):
            rows.append(matrix[i])
            if rank(rows,exp.p)>=exp.n:t=k;break
        times.append(t)
    return {"expected_regions":mean(times),"min":min(times),"max":max(times)}

def analyze(exp, *, q=.9, trials=1200, seed=None):
    q=float(q);trials=max(50,int(trials));seed=exp.seed+1701 if seed is None else int(seed)
    sys=_simulate_systematic(exp,q,trials,seed)
    try: spe=_simulate_spectral(exp,q,trials,seed+1)
    except ValueError as exc: spe={"unavailable":str(exc)}
    return {"approach":ID,"name":NAME,"parameters":{"survival_probability":q,"trials":trials,"seed":seed},
            "systematic":sys,"spectral":spe,"stopping_time_systematic":_stopping_systematic(exp,min(trials,800),seed+2),
            "interpretation":"Probability complements worst-case distance/rank by measuring how often a sufficient region family survives under a specified stochastic failure law."}
