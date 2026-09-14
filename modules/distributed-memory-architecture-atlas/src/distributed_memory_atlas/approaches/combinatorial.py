from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json, zlib
from ..core.combinatorics import capacity, systematic_supports, normalize_layers
from ..core.aggregation import aggregate
from ..core.finite_field import rank, matvec

ID="combinatorial"; NAME="Combinatorial"

def _crc(v: Any) -> str:
    raw=json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":"),default=str).encode()
    return f"{zlib.crc32(raw)&0xffffffff:08x}"

def systematic_matrix(n:int, mode:str, region_limit:int|None=None):
    supports=systematic_supports(n,mode,region_limit=region_limit)
    return [[1 if j in s else 0 for j in range(n)] for s in supports], supports

def _minimum_distance_binary(matrix, n:int, max_n:int=16):
    if n>max_n: return None
    best=len(matrix)+1; witness=None
    for mask in range(1,1<<n):
        x=[(mask>>i)&1 for i in range(n)]
        y=matvec(matrix,x,2)
        w=sum(v&1 for v in y)
        if w<best:
            best=w; witness=x
            if best==1: break
    return {"distance":best,"witness":witness,"detect":best-1,"correct":max(0,(best-1)//2),"erase":best-1}

def analyze(exp, *, preview_limit=120):
    n=exp.n
    declared=max(n,capacity(exp.mode,n))
    matrix,supports=systematic_matrix(n,exp.mode)
    regions=[]
    for rid,s in enumerate(supports,1):
        vals=[exp.token[i] for i in s]
        value=vals[0] if len(s)==1 and rid<=n else aggregate(vals,exp.aggregation)
        regions.append({"id":rid,"kind":"data" if rid<=n else "aggregate","contributors":[i+1 for i in s],"value":value,"checksum":_crc(value)})
    r=rank(matrix, exp.p)
    degrees=[sum(i in s for s in supports) for i in range(n)]
    return {
        "approach":ID,"name":NAME,
        "summary":{
            "n":n,"mode":exp.mode,"layers":list(normalize_layers(exp.mode)),"declared_capacity":declared,
            "physical_regions":len(regions),"data_regions":n,"aggregate_regions":max(0,len(regions)-n),
            "rank_over_field":r,"field":f"F_{exp.p}","rate_dimension_per_region":n/len(regions) if regions else 0,
            "min_degree":min(degrees) if degrees else 0,"max_degree":max(degrees) if degrees else 0,
        },
        "coding":{
            "systematic_matrix_shape":[len(matrix),n],
            "minimum_distance_binary":_minimum_distance_binary(matrix,n),
        },
        "regions":regions[:preview_limit],"region_preview_truncated":len(regions)>preview_limit,
        "supports":[[i+1 for i in s] for s in supports[:preview_limit]],
        "interpretation":"The token is stored systematically in n direct regions; the remaining M/Q/R capacity is filled by contributor subsets. Rank describes algebraic recoverability while region incidence describes the combinatorial geometry."
    }
