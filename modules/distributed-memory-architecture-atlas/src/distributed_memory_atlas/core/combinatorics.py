from __future__ import annotations
from itertools import combinations
from math import comb
from typing import Iterable

MODE_LAYERS = {"M": (0, 2, 4), "Q": (0, 1, 2), "R": (0, 2, 3)}

def normalize_layers(mode: str, custom_layers: Iterable[int] | None = None) -> tuple[int, ...]:
    mode = mode.upper()
    if mode == "CUSTOM":
        if custom_layers is None:
            raise ValueError("custom mode requires custom_layers")
        layers = tuple(sorted(set(int(k) for k in custom_layers if int(k) >= 0)))
        if not layers:
            raise ValueError("custom layer set cannot be empty")
        return layers
    if mode not in MODE_LAYERS:
        raise ValueError("mode must be M, Q, R, or CUSTOM")
    return MODE_LAYERS[mode]

def capacity_from_layers(n: int, layers: Iterable[int]) -> int:
    return sum(comb(n, k) for k in sorted(set(int(x) for x in layers)) if 0 <= k <= n)

def capacity(mode: str, n: int, custom_layers: Iterable[int] | None = None) -> int:
    return capacity_from_layers(n, normalize_layers(mode, custom_layers))

def contributor_sequence(n: int, num_needed: int) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for size in range(2, n + 1):
        for subset in combinations(range(n), size):
            out.append(subset)
            if len(out) >= num_needed:
                return out
    return out

def systematic_supports(n: int, mode: str, custom_layers=None, region_limit: int | None = None) -> list[tuple[int, ...]]:
    total = max(n, capacity(mode, n, custom_layers))
    if region_limit is not None:
        total = min(total, max(n, int(region_limit)))
    out = [(i,) for i in range(n)]
    out.extend(contributor_sequence(n, max(0, total - n)))
    return out

def region_subsets(n: int, mode: str, custom_layers=None, include_empty: bool = True) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for k in normalize_layers(mode, custom_layers):
        if k > n or (k == 0 and not include_empty):
            continue
        out.extend(combinations(range(n), k))
    return out

def cover_regions(n: int, mode: str, region_limit: int | None = None) -> list[tuple[int, ...]]:
    regs = region_subsets(n, mode, include_empty=False)
    if region_limit is not None:
        regs = regs[:max(1, int(region_limit))]
    covered = {i for s in regs for i in s}
    for i in range(n):
        if i not in covered:
            regs.append((i,))
    return regs
