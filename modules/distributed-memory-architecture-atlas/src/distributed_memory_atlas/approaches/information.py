from __future__ import annotations
import math,random
from statistics import mean
from ..core.finite_field import rank
from .combinatorial import systematic_matrix

ID="information";NAME="Information-Theoretic"

def source_entropy(n,p):return n*math.log2(p)
def rank_information(r,p):return r*math.log2(p)
def conditional_entropy(n,r,p):return (n-r)*math.log2(p)
def _binary_entropy(x):
    if x in (0,1):return 0.0
    return -x*math.log2(x)-(1-x)*math.log2(1-x)
def _qentropy(d,p):return 0 if d<=0 else _binary_entropy(d)+d*math.log2(p-1)
def qary_capacity(p,e):
    e=max(0,min(e,(p-1)/p));return max(0,math.log2(p)-_qentropy(e,p))
def qary_rate_distortion(p,d):
    d=max(0,min(d,(p-1)/p));return max(0,math.log2(p)-_qentropy(d,p))
def _greedy(matrix,p):
    rem=set(range(len(matrix)));chosen=[];rr=0;out=[]
    while rem:
        best=None;br=rr
        for i in rem:
            tr=rank([matrix[j] for j in chosen+[i]],p)
            if best is None or tr>br:best,br=i,tr
        if best is None:break
        rem.remove(best);chosen.append(best);gain=br-rr;rr=br
        out.append({"step":len(chosen),"region":best+1,"rank":rr,"rank_gain":gain,"information_gain_bits":rank_information(gain,p),"cumulative_information_bits":rank_information(rr,p)})
    return out

def _survival(matrix,n,p,q,trials,seed):
    rng=random.Random(seed);rs=[]
    for _ in range(trials):
        rows=[x for x in matrix if rng.random()<q];rs.append(rank(rows,p) if rows else 0)
    er=mean(rs)
    return {"q":q,"trials":trials,"expected_rank":er,"expected_mutual_information_bits":rank_information(er,p),"expected_conditional_entropy_bits":conditional_entropy(n,er,p),"full_recovery_probability":sum(r==n for r in rs)/trials}

def analyze(exp, *, q=.9, trials=1000):
    matrix,supports=systematic_matrix(exp.n,exp.mode);r=rank(matrix,exp.p);H=source_entropy(exp.n,exp.p)
    maxe=(exp.p-1)/exp.p
    curve=[{"error":maxe*j/20,"capacity_bits_per_symbol":qary_capacity(exp.p,maxe*j/20)} for j in range(21)]
    rd=[{"distortion":maxe*j/20,"rate_bits_per_symbol":qary_rate_distortion(exp.p,maxe*j/20)} for j in range(21)]
    return {"approach":ID,"name":NAME,
            "summary":{"rank":r,"source_entropy_bits":H,"capacity_bits":rank_information(r,exp.p),"conditional_entropy_bits":conditional_entropy(exp.n,r,exp.p),"regions":len(matrix),"storage_redundancy_factor":len(matrix)/r if r else None,"rate_dimension_per_region":r/len(matrix) if matrix else 0},
            "greedy_profile":_greedy(matrix,exp.p),"survival_information":_survival(matrix,exp.n,exp.p,float(q),max(50,int(trials)),exp.seed+5001),
            "channel_capacity_curve":curve,"rate_distortion_curve":rd,
            "interpretation":"For a uniform source T in F_p^n observed through linear rows of rank r, the observation reveals exactly r log2(p) bits and leaves (n-r) log2(p) bits of conditional entropy. Channel and rate-distortion curves are classical benchmarks, not measured operational capacity of the full architecture."}
