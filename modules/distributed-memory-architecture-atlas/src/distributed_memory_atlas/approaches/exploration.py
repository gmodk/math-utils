from __future__ import annotations

"""Shared exploration payloads for the Atlas research workspaces.

This module deliberately contains *presentation-neutral* mathematical data:
coordinate geometry, region universes and incidence graphs.  The browser owns
rendering, layout, TDA overlays and interaction.
"""

from math import log2
from typing import Any

from ..core.aggregation import aggregate
from ..core.combinatorics import systematic_supports, cover_regions, region_subsets
from ..core.finite_field import rank
from ..core.polynomial import residues
from . import combinatorial, spectral, sheaf

APPROACHES = {"combinatorial", "spectral", "probabilistic", "sheaf", "information"}


def _safe_value(value: Any, maxlen: int = 140) -> Any:
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        return value if len(value) <= maxlen else value[: maxlen - 1] + "…"
    if isinstance(value, list):
        return value if len(value) <= 12 else value[:12] + ["…"]
    if isinstance(value, dict):
        keys = list(value)[:10]
        return {k: value[k] for k in keys}
    return str(value)[:maxlen]


def _spectral_regions(exp):
    n, p = exp.n, exp.p
    if p <= n:
        raise ValueError("spectral exploration requires prime p > n for the default CRT points")
    coeff = [int(x) % p for x in exp.field_projection]
    points = list(range(1, n + 1))
    y = residues(coeff, points, p)
    raw = []
    for rid, s in enumerate(region_subsets(n, exp.mode), 1):
        if len(s) == 0:
            raw.append({"id": rid, "kind": "anchor", "subset0": s, "rows": [], "active": True, "value": coeff[0] if coeff else 0})
        elif len(s) == 1:
            raw.append({"id": rid, "kind": "share", "subset0": s, "rows": [], "active": exp.spectral_policy == "full", "value": y[s[0]]})
        else:
            rows = spectral._constraint_rows([y[i] for i in s], s, n, p)
            raw.append({"id": rid, "kind": "spectral", "subset0": s, "rows": rows, "active": exp.spectral_policy == "full", "value": None})
    if exp.spectral_policy == "rank-basis":
        selected = {r["id"] for r in raw if r["kind"] == "anchor"}
        current: list[list[int]] = []
        rr = 0
        target = max(0, n - 1)
        candidates = [r for r in raw if r["kind"] == "spectral" and r["rows"]]
        while rr < target:
            best = None
            best_rank = rr
            for r in candidates:
                tr = rank(current + r["rows"], p)
                if tr > best_rank:
                    best, best_rank = r, tr
                elif tr == best_rank and tr > rr and best is not None and (len(r["subset0"]), r["id"]) < (len(best["subset0"]), best["id"]):
                    best = r
            if best is None:
                break
            selected.add(best["id"])
            current += best["rows"]
            rr = rank(current, p)
            candidates.remove(best)
        for r in raw:
            r["active"] = r["id"] in selected
    return raw, points, y, coeff


def _systematic_regions(exp, approach: str, q: float):
    matrix, supports = combinatorial.systematic_matrix(exp.n, exp.mode)
    regions = []
    full_rank = rank(matrix, exp.p)
    logp = log2(exp.p)
    # Coordinate degrees are useful for graph/geometry importance without doing
    # an O(N^2) criticality computation.
    degrees = [sum(i in s for s in supports) for i in range(exp.n)]
    max_degree = max(degrees) if degrees else 1
    for idx, (row, s) in enumerate(zip(matrix, supports), 1):
        kind = "data" if idx <= exp.n else "aggregate"
        vals = [exp.token[i] for i in s]
        if vals:
            value = vals[0] if len(s) == 1 and idx <= exp.n else aggregate(vals, exp.aggregation)
        else:
            value = None
        if approach == "probabilistic":
            role = "survival block"
            # Exposure is a visualization/filtration score, not failure probability.
            metric = (1.0 - q) * (sum(degrees[i] for i in s) / (max(1, len(s)) * max_degree))
        elif approach == "information":
            role = "observation row"
            # The systematic identity rows are the earliest independent observations;
            # later rows may still substitute under erasures but are redundant at full state.
            metric = (idx - 1) / max(1, len(supports) - 1)
        else:
            role = kind
            metric = len(s) / max(1, exp.n)
        regions.append({
            "id": idx, "kind": kind, "role": role, "subset0": s, "rows": [row],
            "active": True, "value": _safe_value(value), "integrity": "valid",
            "approach_metric": float(max(0.0, min(1.0, metric))),
            "row_rank": rank([row], exp.p), "information_bits": rank([row], exp.p) * logp,
            "full_rank": full_rank,
        })
    return regions


def _sheaf_regions(exp):
    regs = cover_regions(exp.n, exp.mode, None)
    sections = [[exp.field_projection[i] % exp.p for i in s] for s in regs]
    coord_degree = [sum(i in s for s in regs) for i in range(exp.n)]
    maxd = max(coord_degree) if coord_degree else 1
    out = []
    for rid, (s, sec) in enumerate(zip(regs, sections), 1):
        centrality = sum(coord_degree[i] for i in s) / max(1, len(s) * maxd)
        out.append({
            "id": rid, "kind": "stalk", "role": "local section", "subset0": s,
            "rows": [], "active": True, "value": sec, "section": sec,
            "integrity": "compatible", "approach_metric": float(centrality),
        })
    return out


def region_model(exp, approach: str, q: float = 0.9):
    approach = str(approach).lower()
    if approach not in APPROACHES:
        raise KeyError(approach)
    if approach == "spectral":
        raw, points, y, coeff = _spectral_regions(exp)
        m = max(1, len(raw) - 1)
        for r in raw:
            r["role"] = r["kind"]
            r["integrity"] = "valid"
            r["approach_metric"] = 0.05 * (r["id"] - 1) / m if r["active"] else 0.55 + 0.45 * (r["id"] - 1) / m
            r["row_rank"] = rank(r["rows"], exp.p) if r["rows"] else 0
        coords = [
            {"id": i + 1, "label": f"C{i+1}", "alpha": points[i], "value": y[i], "source": coeff[i]}
            for i in range(exp.n)
        ]
        return raw, coords
    if approach == "sheaf":
        raw = _sheaf_regions(exp)
    else:
        raw = _systematic_regions(exp, approach, q)
    coords = [
        {"id": i + 1, "label": f"C{i+1}", "value": exp.field_projection[i] % exp.p, "source": _safe_value(exp.token[i])}
        for i in range(exp.n)
    ]
    return raw, coords


def _public_region(r):
    return {
        "id": r["id"], "kind": r.get("kind", "region"), "role": r.get("role", r.get("kind", "region")),
        "state": "physical" if r.get("active", True) else "virtual",
        "active": bool(r.get("active", True)), "subset": [i + 1 for i in r.get("subset0", ())],
        "size": len(r.get("subset0", ())), "integrity": r.get("integrity", "valid"),
        "value": _safe_value(r.get("value")), "row_rank": r.get("row_rank"),
        "information_bits": r.get("information_bits"), "approach_metric": r.get("approach_metric", 0.0),
    }


def geometry_payload(exp, approach: str, *, q: float = 0.9, offset: int = 0, limit: int = 80):
    raw, coords = region_model(exp, approach, q)
    offset = max(0, int(offset)); limit = max(1, min(500, int(limit)))
    page = raw[offset: offset + limit]
    active = sum(bool(r.get("active", True)) for r in raw)
    subtitles = {
        "combinatorial": "Coordinates lie on a common circle; each region is a contributor subset in the systematic memory.",
        "spectral": "CRT coordinates lie on the circle; each hyperedge carries a local invariant-subspace constraint.",
        "probabilistic": "The same region geometry is viewed as a family of random survival blocks under an erasure law.",
        "sheaf": "Regions are local patches; overlaps define the nerve and restriction consistency of local sections.",
        "information": "Regions are observations of the token; incidence geometry determines which coordinates each observation couples.",
    }
    return {
        "approach": approach, "coordinates": coords, "regions": [_public_region(r) for r in page],
        "total": len(raw), "offset": offset, "limit": limit,
        "summary": {"n": exp.n, "p": exp.p, "mode": exp.mode, "regions": len(raw), "physical": active, "virtual": len(raw)-active},
        "subtitle": subtitles[approach],
    }


def region_detail(exp, approach: str, rid: int, *, q: float = 0.9):
    raw, _ = region_model(exp, approach, q)
    if rid < 1 or rid > len(raw):
        raise KeyError(f"region {rid}")
    r = raw[rid - 1]
    base = _public_region(r)
    s = r.get("subset0", ())
    if approach == "spectral":
        base.update({"constraint_rows": r.get("rows", []), "constraint_rank": rank(r.get("rows", []), exp.p) if r.get("rows") else 0,
                     "meaning": "Local spectral block; its lifted rows constrain the global CRT vector."})
    elif approach == "combinatorial":
        base.update({"contributors": [i+1 for i in s], "meaning": "Systematic contributor region; direct rows store coordinates and aggregate rows couple contributors."})
    elif approach == "probabilistic":
        base.update({"survival_probability": q, "failure_probability": 1-q,
                     "meaning": "Random survival block. Recovery is evaluated from the rank of all surviving observation rows."})
    elif approach == "sheaf":
        overlaps = []
        for other in raw:
            if other["id"] == r["id"]: continue
            inter = sorted(set(s) & set(other.get("subset0", ())))
            if inter: overlaps.append({"region": other["id"], "intersection": [i+1 for i in inter]})
        base.update({"section": r.get("section", []), "overlaps": overlaps[:80],
                     "meaning": "Local section on a cover patch. Overlaps determine restriction comparisons and nerve simplices."})
    else:
        base.update({"single_observation_information_bits": r.get("information_bits", 0),
                     "meaning": "Linear observation row. Joint information is governed by rank, not by adding single-row information blindly."})
    return base


def graph_payload(exp, approach: str, *, active_only: bool = True, q: float = 0.9, limit: int = 1600):
    raw, coords = region_model(exp, approach, q)
    selected = [r for r in raw if (r.get("active", True) or not active_only)]
    truncated = len(selected) > limit
    selected = selected[:limit]
    nodes = [{"id": f"C{c['id']}", "kind": "coordinate", "label": c["label"], "value": c.get("value"), "alpha": c.get("alpha"), "reference_value": c.get("value"), "filtration": 0.0} for c in coords]
    edges = []
    for r in selected:
        nodes.append({
            "id": f"R{r['id']}", "kind": r.get("kind", "region"), "label": f"R{r['id']}",
            "active": bool(r.get("active", True)), "role": r.get("role"), "subset_size": len(r.get("subset0", ())),
            "filtration": float(r.get("approach_metric", 0.0)), "approach": approach,
        })
        for idx in r.get("subset0", ()):
            edges.append({"source": f"C{idx+1}", "target": f"R{r['id']}"})
    return {"nodes": nodes, "edges": edges, "truncated": truncated, "total_regions": len(raw), "rendered_regions": len(selected), "approach": approach}
