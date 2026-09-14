from __future__ import annotations

"""Linear secret sharing and monotone span programs for the Atlas.

The implementation uses a large prime field so a 256-bit AEAD key can be
embedded as one field element.  The module implements two policy families:

* threshold MSPs (Shamir/Vandermonde form), and
* DNF access structures compiled from minimal authorized region sets.

For a matrix M with row labels rho and vector z=(s,r_1,...,r_m), shares are
M z.  A coalition A is authorized iff e_1 lies in the span of the rows whose
labels belong to A.  Under uniform fresh masks, an unauthorized coalition has
perfect information-theoretic secrecy for the scalar secret.
"""

from dataclasses import dataclass
from secrets import randbelow
from typing import Iterable, Sequence

# 2^521-1 is a Mersenne prime.  It is comfortably larger than a 256-bit key.
LSSS_PRIME = (1 << 521) - 1


def _inv(a: int, p: int) -> int:
    a %= p
    if not a:
        raise ZeroDivisionError("zero is not invertible")
    return pow(a, -1, p)


def _dot(a: Sequence[int], b: Sequence[int], p: int) -> int:
    return sum((int(x) % p) * (int(y) % p) for x, y in zip(a, b)) % p


def _solve_linear(a: Sequence[Sequence[int]], b: Sequence[int], p: int) -> list[int] | None:
    """Return one solution to A x=b over F_p, or None when inconsistent."""
    if len(a) != len(b):
        raise ValueError("equation count mismatch")
    if not a:
        return [] if not b else None
    cols = len(a[0])
    aug = [[int(x) % p for x in row] + [int(rhs) % p] for row, rhs in zip(a, b)]
    if any(len(row) != cols + 1 for row in aug):
        raise ValueError("matrix row width mismatch")
    r = 0
    pivots: list[int] = []
    for c in range(cols):
        pivot = next((i for i in range(r, len(aug)) if aug[i][c] % p), None)
        if pivot is None:
            continue
        aug[r], aug[pivot] = aug[pivot], aug[r]
        scale = _inv(aug[r][c], p)
        aug[r] = [(scale * x) % p for x in aug[r]]
        for i in range(len(aug)):
            if i == r:
                continue
            f = aug[i][c] % p
            if f:
                aug[i] = [(x - f * y) % p for x, y in zip(aug[i], aug[r])]
        pivots.append(c)
        r += 1
        if r == len(aug):
            break
    for row in aug:
        if all(x % p == 0 for x in row[:-1]) and row[-1] % p:
            return None
    x = [0] * cols
    for i, c in enumerate(pivots):
        x[c] = aug[i][-1] % p
    return x


@dataclass(frozen=True)
class SpanProgram:
    matrix: list[list[int]]
    labels: list[int]
    prime: int = LSSS_PRIME
    name: str = "LSSS"
    metadata: dict | None = None

    @property
    def width(self) -> int:
        return len(self.matrix[0]) if self.matrix else 1

    @property
    def participants(self) -> list[int]:
        return sorted(set(self.labels))

    def rows_for(self, coalition: Iterable[int]) -> tuple[list[int], list[list[int]]]:
        chosen = set(int(x) for x in coalition)
        idx = [i for i, label in enumerate(self.labels) if label in chosen]
        return idx, [self.matrix[i] for i in idx]

    def reconstruction_coefficients(self, coalition: Iterable[int]) -> tuple[list[int], list[int]] | None:
        idx, rows = self.rows_for(coalition)
        if not rows:
            return None
        # Need lambda with lambda^T rows = e_1^T; equivalently rows^T lambda=e_1.
        equations = [[rows[j][i] for j in range(len(rows))] for i in range(self.width)]
        target = [1] + [0] * (self.width - 1)
        coeff = _solve_linear(equations, target, self.prime)
        return (idx, coeff) if coeff is not None else None

    def authorized(self, coalition: Iterable[int]) -> bool:
        return self.reconstruction_coefficients(coalition) is not None


def threshold_span_program(participants: Sequence[int], threshold: int, p: int = LSSS_PRIME) -> SpanProgram:
    ids = [int(x) for x in participants]
    if len(set(ids)) != len(ids) or not ids:
        raise ValueError("participants must be a non-empty set of unique region IDs")
    t = int(threshold)
    if not (1 <= t <= len(ids)):
        raise ValueError("threshold must satisfy 1 <= t <= number of participants")
    matrix = []
    for j in range(1, len(ids) + 1):
        matrix.append([pow(j, k, p) for k in range(t)])
    return SpanProgram(matrix, ids, p, f"{t}-of-{len(ids)} threshold LSSS", {"type": "threshold", "threshold": t})


def dnf_span_program(minimal_authorized_sets: Sequence[Sequence[int]], p: int = LSSS_PRIME) -> SpanProgram:
    """Compile OR-of-AND minimal sets into an explicit LSSS.

    Each AND-clause independently additive-shares the same secret.  A region may
    receive multiple rows when it occurs in multiple clauses.  The construction
    is intentionally simple and transparent rather than share-size optimal.
    """
    clauses: list[tuple[int, ...]] = []
    for raw in minimal_authorized_sets:
        clause = tuple(sorted(set(int(x) for x in raw)))
        if not clause:
            raise ValueError("authorized sets cannot be empty")
        if clause not in clauses:
            clauses.append(clause)
    if not clauses:
        raise ValueError("at least one minimal authorized set is required")
    # Remove clauses that are supersets of another clause; they are not minimal.
    clauses = [c for c in clauses if not any(set(d) < set(c) for d in clauses)]
    random_cols = sum(max(0, len(c) - 1) for c in clauses)
    width = 1 + random_cols
    matrix: list[list[int]] = []
    labels: list[int] = []
    cursor = 1
    for clause in clauses:
        if len(clause) == 1:
            row = [0] * width
            row[0] = 1
            matrix.append(row); labels.append(clause[0])
            continue
        local_cols = list(range(cursor, cursor + len(clause) - 1))
        cursor += len(clause) - 1
        for region, col in zip(clause[:-1], local_cols):
            row = [0] * width
            row[col] = 1
            matrix.append(row); labels.append(region)
        row = [0] * width
        row[0] = 1
        for col in local_cols:
            row[col] = (-1) % p
        matrix.append(row); labels.append(clause[-1])
    return SpanProgram(matrix, labels, p, "DNF monotone-span LSSS", {"type": "dnf", "minimal_authorized_sets": [list(c) for c in clauses]})


def share_secret(secret: int, program: SpanProgram) -> list[dict]:
    p = program.prime
    secret = int(secret)
    if not (0 <= secret < p):
        raise ValueError("secret must be one field element")
    vector = [secret] + [randbelow(p) for _ in range(program.width - 1)]
    out = []
    occurrence: dict[int, int] = {}
    for row_id, (label, row) in enumerate(zip(program.labels, program.matrix), 1):
        occurrence[label] = occurrence.get(label, 0) + 1
        out.append({
            "row_id": row_id,
            "region": label,
            "occurrence": occurrence[label],
            "value": _dot(row, vector, p),
        })
    return out


def reconstruct_secret(program: SpanProgram, shares: Sequence[dict], coalition: Iterable[int]) -> int | None:
    rec = program.reconstruction_coefficients(coalition)
    if rec is None:
        return None
    idx, coeff = rec
    by_row = {int(s["row_id"]): int(s["value"]) % program.prime for s in shares}
    values = []
    for i in idx:
        row_id = i + 1
        if row_id not in by_row:
            return None
        values.append(by_row[row_id])
    return sum(c * v for c, v in zip(coeff, values)) % program.prime


def policy_summary(program: SpanProgram) -> dict:
    return {
        "name": program.name,
        "type": (program.metadata or {}).get("type", "matrix"),
        "participants": program.participants,
        "participant_count": len(program.participants),
        "share_rows": len(program.matrix),
        "span_dimension": program.width,
        "field": "F_(2^521-1)",
        "threshold": (program.metadata or {}).get("threshold"),
        "minimal_authorized_sets": (program.metadata or {}).get("minimal_authorized_sets"),
    }
