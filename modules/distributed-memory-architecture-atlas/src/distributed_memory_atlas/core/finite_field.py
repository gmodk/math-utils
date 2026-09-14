"""Finite-field linear algebra over prime fields F_p.

The project intentionally stays dependency-free.  This module implements the
small exact operations needed by the spectral-memory explorer: modular matrix
arithmetic, RREF, rank, nullspaces, inverses and square solves.
"""
from __future__ import annotations

from math import isqrt
from typing import Iterable, Sequence

Matrix = list[list[int]]
Vector = list[int]


def is_prime(p: int) -> bool:
    if p < 2:
        return False
    if p in (2, 3):
        return True
    if p % 2 == 0:
        return False
    r = isqrt(p)
    d = 3
    while d <= r:
        if p % d == 0:
            return False
        d += 2
    return True


def require_prime(p: int) -> int:
    p = int(p)
    if not is_prime(p):
        raise ValueError(f"field modulus must be prime; got {p}")
    return p


def mod(x: int, p: int) -> int:
    return int(x) % p


def inv(a: int, p: int) -> int:
    a %= p
    if a == 0:
        raise ZeroDivisionError("0 has no multiplicative inverse in F_p")
    return pow(a, -1, p)


def identity(n: int) -> Matrix:
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def zeros(r: int, c: int) -> Matrix:
    return [[0 for _ in range(c)] for _ in range(r)]


def transpose(a: Sequence[Sequence[int]]) -> Matrix:
    if not a:
        return []
    return [list(row) for row in zip(*a)]


def matmul(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]], p: int) -> Matrix:
    if not a or not b:
        return []
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) % p for col in bt] for row in a]


def matvec(a: Sequence[Sequence[int]], v: Sequence[int], p: int) -> Vector:
    return [sum(x * y for x, y in zip(row, v)) % p for row in a]


def matsub(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]], p: int) -> Matrix:
    return [[(x - y) % p for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def matadd(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]], p: int) -> Matrix:
    return [[(x + y) % p for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def scalar_mul(c: int, a: Sequence[Sequence[int]], p: int) -> Matrix:
    return [[c * x % p for x in row] for row in a]


def outer(u: Sequence[int], v: Sequence[int], p: int) -> Matrix:
    return [[x * y % p for y in v] for x in u]


def rref(a: Sequence[Sequence[int]], p: int) -> tuple[Matrix, list[int]]:
    if not a:
        return [], []
    m = [[int(x) % p for x in row] for row in a]
    rows, cols = len(m), len(m[0])
    pivots: list[int] = []
    r = 0
    for c in range(cols):
        pivot = next((i for i in range(r, rows) if m[i][c] % p), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        scale = inv(m[r][c], p)
        m[r] = [(scale * x) % p for x in m[r]]
        for i in range(rows):
            if i == r:
                continue
            factor = m[i][c] % p
            if factor:
                m[i] = [(x - factor * y) % p for x, y in zip(m[i], m[r])]
        pivots.append(c)
        r += 1
        if r == rows:
            break
    return m, pivots


def rank(a: Sequence[Sequence[int]], p: int) -> int:
    return len(rref(a, p)[1]) if a else 0


def nullspace(a: Sequence[Sequence[int]], p: int, ncols: int | None = None) -> list[Vector]:
    if not a:
        if ncols is None:
            return []
        return [row[:] for row in identity(ncols)]
    rr, pivots = rref(a, p)
    cols = len(rr[0]) if ncols is None else ncols
    free = [c for c in range(cols) if c not in pivots]
    basis: list[Vector] = []
    for f in free:
        v = [0] * cols
        v[f] = 1
        for row_i, pivot_col in enumerate(pivots):
            if pivot_col < cols:
                v[pivot_col] = (-rr[row_i][f]) % p
        basis.append(v)
    return basis


def inverse(a: Sequence[Sequence[int]], p: int) -> Matrix:
    n = len(a)
    if n == 0 or any(len(row) != n for row in a):
        raise ValueError("matrix must be non-empty and square")
    aug = [[int(x) % p for x in row] + ident for row, ident in zip(a, identity(n))]
    rr, pivots = rref(aug, p)
    if pivots[:n] != list(range(n)):
        raise ValueError("matrix is singular over F_p")
    return [row[n:] for row in rr]


def solve_square(a: Sequence[Sequence[int]], b: Sequence[int], p: int) -> Vector:
    n = len(a)
    if len(b) != n:
        raise ValueError("right-hand side has wrong length")
    inva = inverse(a, p)
    return matvec(inva, b, p)


def stack(rows: Iterable[Sequence[int]], ncols: int | None = None) -> Matrix:
    out = [list(r) for r in rows]
    if out:
        width = len(out[0])
        if any(len(r) != width for r in out):
            raise ValueError("row width mismatch")
    elif ncols is not None:
        return []
    return out


def vector_scale(c: int, v: Sequence[int], p: int) -> Vector:
    return [(c * x) % p for x in v]


def vector_equal_up_to_scale(a: Sequence[int], b: Sequence[int], p: int) -> bool:
    if len(a) != len(b):
        return False
    pivot = next((i for i, x in enumerate(a) if x % p), None)
    if pivot is None:
        return all(x % p == 0 for x in b)
    if b[pivot] % p == 0:
        return False
    c = b[pivot] * inv(a[pivot], p) % p
    return all((c * x - y) % p == 0 for x, y in zip(a, b))
