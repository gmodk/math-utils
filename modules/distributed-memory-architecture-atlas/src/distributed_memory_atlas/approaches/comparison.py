from __future__ import annotations
from . import combinatorial,spectral,probabilistic,sheaf,information

ID="comparison";NAME="Cross-Approach Comparison"
def analyze(exp, *, q=.9, trials=600):
    c=combinatorial.analyze(exp,preview_limit=20)
    try:s=spectral.analyze(exp,preview_limit=20)
    except Exception as exc:s={"error":str(exc),"summary":{}}
    p=probabilistic.analyze(exp,q=q,trials=trials)
    h=sheaf.analyze(exp)
    i=information.analyze(exp,q=q,trials=trials)
    cs=c["summary"];ss=s.get("summary",{});hs=h["cohomology"];ins=i["summary"]
    rows=[
        {"lens":"Combinatorial","primary":"regions","value":cs.get("physical_regions"),"secondary":f"rank {cs.get('rank_over_field')} / {exp.n}"},
        {"lens":"Spectral","primary":"physical constraints","value":ss.get("physical_regions","n/a"),"secondary":f"rank {ss.get('constraint_rank','n/a')} / {ss.get('target_rank','n/a')}"},
        {"lens":"Probabilistic","primary":f"P(recovery), q={q}","value":round(p["systematic"]["recovery_probability"],4),"secondary":"systematic survival law"},
        {"lens":"Sheaf","primary":"dim H^0","value":hs["cohomology_dimensions"][0] if hs["cohomology_dimensions"] else 0,"secondary":f"H^1={hs['cohomology_dimensions'][1] if len(hs['cohomology_dimensions'])>1 else 'n/a'}"},
        {"lens":"Information","primary":"source entropy (bits)","value":round(ins["source_entropy_bits"],4),"secondary":f"revealed {round(ins['capacity_bits'],4)} bits"},
    ]
    return {"approach":ID,"name":NAME,"rows":rows,
            "bridge_invariants":{"systematic_rank":cs.get("rank_over_field"),"information_rank":ins.get("rank"),"rank_information_identity_holds":cs.get("rank_over_field")==ins.get("rank"),"spectral_projective_recovery":ss.get("projectively_recoverable"),"sheaf_compatible":h["compatibility"]["compatible"]},
            "note":"These quantities answer different questions and should not be interpreted as a single scalar score. The comparison lab exposes correspondences and threshold coincidences across mathematical lenses."}
