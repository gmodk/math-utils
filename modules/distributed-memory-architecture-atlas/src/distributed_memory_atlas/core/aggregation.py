from __future__ import annotations
from typing import Any

def compose_permutations(perms):
    if not perms:
        return []
    out = list(range(len(perms[0])))
    for f in perms:
        if len(f) != len(out):
            raise ValueError("all permutations must have the same degree")
        out = [f[out[i]] for i in range(len(out))]
    return out

def aggregate(values: list[Any], method: str = "mixed") -> Any:
    method = method.lower()
    if not values:
        return None
    if method == "compose":
        return compose_permutations(values)
    if method == "sum":
        return sum(values)
    if method == "product":
        out = 1
        for v in values: out *= v
        return out
    if method == "concat":
        return " | ".join(str(v) for v in values)
    # Mixed is intentionally type-aware and JSON-safe.
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        return sum(values)
    if all(isinstance(v, str) for v in values):
        return " · ".join(values)
    if all(isinstance(v, list) for v in values) and values and all(len(v) == len(values[0]) for v in values):
        if all(all(isinstance(x, (int, float)) for x in v) for v in values):
            return [sum(v[j] for v in values) for j in range(len(values[0]))]
    return {"kind": "aggregate_tuple", "values": values}
