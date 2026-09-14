"""Core permutation-group algorithms for the S_n Explorer web application.

The module keeps the mathematical convention used by the original CLI:
    (sigma o tau)(i) = sigma(tau(i))
so tau acts first and sigma acts second.

Permutations are represented internally as zero-based lists/tuples but rendered
for humans in one-based notation.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import permutations
from math import gcd
from typing import Iterable, List, Sequence, Tuple

Permutation = List[int]
PermutationTuple = Tuple[int, ...]


# ---------------------------------------------------------------------------
# Basic permutations and S_n
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def permutation_tuples(n: int) -> Tuple[PermutationTuple, ...]:
    if not 1 <= n <= 8:
        raise ValueError("n must satisfy 1 <= n <= 8 for this explorer")
    return tuple(permutations(range(n)))


def generate_permutations(n: int) -> List[Permutation]:
    """Return all n! permutations of {0, ..., n-1} in lexicographic order."""
    return [list(p) for p in permutation_tuples(n)]


def _validate_same_degree(sigma: Sequence[int], tau: Sequence[int]) -> None:
    if len(sigma) != len(tau):
        raise ValueError("Permutations must act on the same n")


def compose(sigma: Sequence[int], tau: Sequence[int]) -> Permutation:
    """Compute sigma o tau, i.e. apply tau first, then sigma."""
    _validate_same_degree(sigma, tau)
    return [sigma[tau[i]] for i in range(len(sigma))]


def identity(n: int) -> Permutation:
    return list(range(n))


def inverse(sigma: Sequence[int]) -> Permutation:
    inv = [0] * len(sigma)
    for i, value in enumerate(sigma):
        inv[value] = i
    return inv


def is_identity(sigma: Sequence[int]) -> bool:
    return list(sigma) == identity(len(sigma))


def is_self_inverse(sigma: Sequence[int]) -> bool:
    return list(sigma) == inverse(sigma)


# ---------------------------------------------------------------------------
# Cycle structure, order and parity
# ---------------------------------------------------------------------------

def cycle_decomposition(
    sigma: Sequence[int], *, exclude_fixed_points: bool = True
) -> List[List[int]]:
    n = len(sigma)
    visited = [False] * n
    cycles: List[List[int]] = []

    for start in range(n):
        if visited[start]:
            continue
        cycle: List[int] = []
        current = start
        while not visited[current]:
            visited[current] = True
            cycle.append(current)
            current = sigma[current]
        if not (exclude_fixed_points and len(cycle) == 1):
            cycles.append(cycle)
    return cycles


def cycle_notation(sigma: Sequence[int]) -> str:
    cycles = cycle_decomposition(sigma, exclude_fixed_points=True)
    if not cycles:
        return "id"
    return "".join("(" + " ".join(str(i + 1) for i in c) + ")" for c in cycles)


def one_line_notation(sigma: Sequence[int]) -> str:
    return "(" + " ".join(str(x + 1) for x in sigma) + ")"


def cycle_type(sigma: Sequence[int]) -> Tuple[int, ...]:
    """Partition of n given by all disjoint-cycle lengths, including 1-cycles."""
    return tuple(
        sorted(
            (len(c) for c in cycle_decomposition(sigma, exclude_fixed_points=False)),
            reverse=True,
        )
    )


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def order(sigma: Sequence[int]) -> int:
    result = 1
    for cycle in cycle_decomposition(sigma, exclude_fixed_points=True):
        result = _lcm(result, len(cycle))
    return result


def sign(sigma: Sequence[int]) -> int:
    s = 1
    for cycle in cycle_decomposition(sigma, exclude_fixed_points=True):
        if (len(cycle) - 1) % 2:
            s = -s
    return s


def order_and_sign(sigma: Sequence[int]) -> Tuple[int, int]:
    cycles = cycle_decomposition(sigma, exclude_fixed_points=True)
    result = 1
    s = 1
    for cycle in cycles:
        result = _lcm(result, len(cycle))
        if (len(cycle) - 1) % 2:
            s = -s
    return result, s


def permutation_record(index: int, sigma: Sequence[int]) -> dict:
    inv = inverse(sigma)
    o, s = order_and_sign(sigma)
    return {
        "index": index,
        "permutation": list(sigma),
        "one_line": one_line_notation(sigma),
        "cycles": cycle_notation(sigma),
        "cycle_type": list(cycle_type(sigma)),
        "order": o,
        "sign": s,
        "parity": "even" if s == 1 else "odd",
        "self_inverse": is_self_inverse(sigma),
        "identity": is_identity(sigma),
        "inverse": inv,
        "inverse_one_line": one_line_notation(inv),
        "inverse_cycles": cycle_notation(inv),
    }


# ---------------------------------------------------------------------------
# Cayley tables
# ---------------------------------------------------------------------------

def cayley_table(elements: Sequence[Sequence[int]]) -> List[List[int]]:
    """Return a zero-based multiplication table for the given finite group."""
    index_of = {tuple(p): k for k, p in enumerate(elements)}
    table: List[List[int]] = []
    for left in elements:
        row: List[int] = []
        for right in elements:
            product = tuple(compose(left, right))
            if product not in index_of:
                raise ValueError("The supplied elements are not closed under composition")
            row.append(index_of[product])
        table.append(row)
    return table


# ---------------------------------------------------------------------------
# Dihedral group D_m as a subgroup of S_m
# ---------------------------------------------------------------------------

def build_dihedral_group(n: int) -> List[dict]:
    if not 3 <= n <= 24:
        raise ValueError("m must satisfy 3 <= m <= 24")

    def rotation_power(k: int) -> Permutation:
        return [(i + k) % n for i in range(n)]

    reflection = [(-i) % n for i in range(n)]
    elements: List[dict] = []

    for k in range(n):
        r_k = rotation_power(k)
        name = "e" if k == 0 else ("r" if k == 1 else f"r^{k}")
        elements.append(
            {
                "permutation": r_k,
                "name": name,
                "type": "rotation",
                "angle_deg": 360.0 * k / n,
            }
        )

    for k in range(n):
        r_k = rotation_power(k)
        sr_k = compose(reflection, r_k)
        name = "s" if k == 0 else ("s r" if k == 1 else f"s r^{k}")
        elements.append(
            {
                "permutation": sr_k,
                "name": name,
                "type": "reflection",
                "angle_deg": None,
            }
        )

    return elements


# ---------------------------------------------------------------------------
# Subgroups and normality
# ---------------------------------------------------------------------------

def generate_subgroup(generators: Sequence[Sequence[int]], n: int) -> List[Permutation]:
    """Generate the closure of the supplied generators under composition."""
    closure = {tuple(identity(n))}
    for generator in generators:
        if len(generator) != n:
            raise ValueError("Every generator must have degree n")
        closure.add(tuple(generator))

    to_process = list(closure)
    while to_process:
        a = list(to_process.pop())
        snapshot = list(closure)
        for b_tuple in snapshot:
            b = list(b_tuple)
            for product in (compose(a, b), compose(b, a)):
                key = tuple(product)
                if key not in closure:
                    closure.add(key)
                    to_process.append(key)

    return [list(t) for t in sorted(closure)]


def all_subgroups(elements: Sequence[Sequence[int]]) -> List[List[Permutation]]:
    if not elements:
        return []
    n = len(elements[0])
    elem_set = {tuple(e) for e in elements}
    trivial = frozenset({tuple(identity(n))})
    found = {trivial: sorted(trivial)}
    frontier = [trivial]

    while frontier:
        next_frontier = []
        for h_key in frontier:
            for g in elem_set:
                if g in h_key:
                    continue
                candidate = generate_subgroup(
                    [list(g)] + [list(x) for x in h_key], n
                )
                key = frozenset(tuple(c) for c in candidate)
                if key not in found:
                    found[key] = sorted(key)
                    next_frontier.append(key)
        frontier = next_frontier

    result = list(found.values())
    result.sort(key=lambda subgroup: (len(subgroup), subgroup))
    return [[list(t) for t in subgroup] for subgroup in result]


@lru_cache(maxsize=8)
def all_subgroups_sn(n: int) -> Tuple[Tuple[PermutationTuple, ...], ...]:
    if n > 4:
        raise ValueError("Exhaustive subgroup enumeration is capped at n <= 4")
    groups = all_subgroups(generate_permutations(n))
    return tuple(tuple(tuple(p) for p in group) for group in groups)


def is_normal_subgroup(
    subgroup: Sequence[Sequence[int]], elements: Sequence[Sequence[int]]
) -> bool:
    subgroup_set = {tuple(h) for h in subgroup}
    for g in elements:
        g_inv = inverse(g)
        for h in subgroup:
            conjugate = compose(compose(g, h), g_inv)
            if tuple(conjugate) not in subgroup_set:
                return False
    return True


# ---------------------------------------------------------------------------
# Quotient groups
# ---------------------------------------------------------------------------

def left_cosets(
    subgroup: Sequence[Sequence[int]], elements: Sequence[Sequence[int]]
) -> List[List[Permutation]]:
    subgroup_tuples = [tuple(h) for h in subgroup]
    remaining = {tuple(g) for g in elements}
    cosets: List[List[PermutationTuple]] = []

    while remaining:
        g = min(remaining)
        coset = sorted(
            tuple(compose(list(g), list(h))) for h in subgroup_tuples
        )
        cosets.append(coset)
        remaining -= set(coset)

    cosets.sort(key=lambda c: c[0])
    return [[list(t) for t in coset] for coset in cosets]


def quotient_group(
    subgroup: Sequence[Sequence[int]], elements: Sequence[Sequence[int]]
) -> dict:
    if not is_normal_subgroup(subgroup, elements):
        raise ValueError("G/H is a group only when H is normal in G")

    cosets = left_cosets(subgroup, elements)
    m = len(cosets)
    coset_of = {}
    for idx, coset in enumerate(cosets):
        for g in coset:
            coset_of[tuple(g)] = idx

    table = [[0] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            product = compose(cosets[i][0], cosets[j][0])
            table[i][j] = coset_of[tuple(product)]

    subgroup_set = {tuple(h) for h in subgroup}
    identity_idx = next(
        idx
        for idx, coset in enumerate(cosets)
        if {tuple(g) for g in coset} == subgroup_set
    )
    return {
        "cosets": cosets,
        "order": m,
        "table": table,
        "identity_idx": identity_idx,
    }


def quotient_element_order(table: Sequence[Sequence[int]], identity_idx: int, elem_idx: int) -> int:
    current = elem_idx
    k = 1
    while current != identity_idx:
        current = table[current][elem_idx]
        k += 1
        if k > len(table) + 1:
            raise RuntimeError("Malformed quotient Cayley table")
    return k


# ---------------------------------------------------------------------------
# Conjugacy classes of S_n
# ---------------------------------------------------------------------------

def conjugacy_class_summaries(n: int) -> List[dict]:
    """Summarize S_n conjugacy classes, which are determined by cycle type."""
    buckets: dict[Tuple[int, ...], List[PermutationTuple]] = {}
    for perm in permutation_tuples(n):
        buckets.setdefault(cycle_type(perm), []).append(perm)

    summaries = []
    for ctype, members in sorted(buckets.items(), reverse=True):
        representative = members[0]
        summaries.append(
            {
                "cycle_type": list(ctype),
                "size": len(members),
                "representative": list(representative),
                "representative_cycles": cycle_notation(representative),
                "order": order(representative),
                "sign": sign(representative),
                "parity": "even" if sign(representative) == 1 else "odd",
            }
        )
    return summaries
