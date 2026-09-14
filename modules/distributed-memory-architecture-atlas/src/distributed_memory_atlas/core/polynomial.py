from __future__ import annotations

def evaluate(coeffs, x: int, p: int) -> int:
    acc = 0
    for c in reversed(coeffs):
        acc = (acc * x + int(c)) % p
    return acc

def residues(coeffs, points, p: int) -> list[int]:
    return [evaluate(coeffs, x, p) for x in points]
