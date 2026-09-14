from __future__ import annotations

import hashlib
import json
import random
import string
from typing import Any

_WORDS = [
    "algebra", "anchor", "basis", "branch", "circle", "code", "cycle", "delta",
    "entropy", "field", "forest", "function", "graph", "group", "kernel", "matrix",
    "measure", "memory", "orbit", "prime", "rank", "region", "section", "sheaf",
    "signal", "simplex", "spectral", "stalk", "state", "subset", "symmetry", "token",
    "vector", "vertex", "random", "probability", "channel", "source", "hypergraph",
    "projector", "polynomial", "residue", "finite", "local", "global", "information",
    "topology", "homology", "cohomology", "restriction", "capacity", "distortion",
    "recovery", "erasure", "invariant", "eigenvector", "coordinate", "permutation",
]

_TOKEN_TYPES = {
    "chars", "words", "integers", "natural_numbers", "vectors", "cyclic_permutations", "functions"
}


def available_token_types() -> list[str]:
    return sorted(_TOKEN_TYPES)


def _stable_hash_mod(value: Any, p: int) -> int:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest(), "big") % p


def _function_expression(coefficients: list[int], p: int) -> str:
    terms: list[str] = []
    for power, coeff in enumerate(coefficients):
        coeff %= p
        if coeff == 0:
            continue
        if power == 0:
            terms.append(str(coeff))
        elif power == 1:
            terms.append(f"{coeff}*x")
        else:
            terms.append(f"{coeff}*x^{power}")
    return (" + ".join(terms) if terms else "0") + f"  (mod {p})"


def _project(value: Any, token_type: str, p: int) -> int:
    if token_type in {"integers", "natural_numbers"}:
        return int(value) % p
    if token_type == "chars":
        return ord(str(value)[0]) % p
    if token_type == "words":
        return _stable_hash_mod(value, p)
    if token_type == "vectors":
        return sum((i + 1) * int(x) for i, x in enumerate(value)) % p
    if token_type == "cyclic_permutations":
        # Every generated permutation is a power c^k of the standard cycle;
        # in one-line notation its first entry equals k.
        return int(value[0]) % p if value else 0
    if token_type == "functions":
        # Evaluate the polynomial at x=1 in F_p.
        return sum(int(x) for x in value["coefficients"]) % p
    return _stable_hash_mod(value, p)


def generate_random_token(
    dimension: int,
    token_type: str,
    *,
    seed: int = 0,
    p: int = 101,
    object_dimension: int | None = None,
    integer_min: int = -100,
    integer_max: int = 100,
    natural_max: int = 100,
) -> dict:
    """Generate a JSON-serializable random token plus a finite-field projection.

    ``dimension`` is the number of token coordinates. For vector-valued entries and
    cyclic permutations, ``object_dimension`` controls the dimension/degree of each
    coordinate and defaults to ``dimension``. For functions, ``object_dimension`` is
    interpreted as the polynomial degree and defaults to 3.
    """
    dimension = int(dimension)
    seed = int(seed)
    p = int(p)
    token_type = str(token_type).strip().lower()
    if dimension < 1:
        raise ValueError("dimension must be >= 1")
    if p < 2:
        raise ValueError("p must be >= 2")
    if token_type not in _TOKEN_TYPES:
        raise ValueError(f"unknown token type: {token_type}")
    rng = random.Random(seed)

    metadata: dict[str, Any] = {}
    if token_type == "chars":
        alphabet = string.ascii_letters
        token = [rng.choice(alphabet) for _ in range(dimension)]
        projection_method = "Unicode code point modulo p"
    elif token_type == "words":
        token = [rng.choice(_WORDS) for _ in range(dimension)]
        projection_method = "SHA-256 canonical-string hash modulo p"
    elif token_type == "integers":
        if integer_min > integer_max:
            raise ValueError("integer_min must be <= integer_max")
        token = [rng.randint(integer_min, integer_max) for _ in range(dimension)]
        metadata.update({"integer_min": integer_min, "integer_max": integer_max})
        projection_method = "integer residue modulo p"
    elif token_type == "natural_numbers":
        if natural_max < 0:
            raise ValueError("natural_max must be >= 0")
        token = [rng.randint(0, natural_max) for _ in range(dimension)]
        metadata.update({"natural_definition": "N = {0,1,2,...}", "natural_max": natural_max})
        projection_method = "natural-number residue modulo p"
    elif token_type == "vectors":
        m = int(object_dimension if object_dimension not in (None, "") else dimension)
        if m < 1:
            raise ValueError("vector component dimension must be >= 1")
        token = [[rng.randint(-9, 9) for _ in range(m)] for _ in range(dimension)]
        metadata.update({"element_dimension": m, "component_range": [-9, 9]})
        projection_method = "weighted coordinate sum sum((j+1)v_j) modulo p"
    elif token_type == "cyclic_permutations":
        m = int(object_dimension if object_dimension not in (None, "") else dimension)
        if m < 1:
            raise ValueError("permutation degree must be >= 1")
        shifts = [rng.randrange(m) for _ in range(dimension)]
        token = [[(i + k) % m for i in range(m)] for k in shifts]
        metadata.update({
            "permutation_degree": m,
            "group": f"C_{m}",
            "representation": "zero-based one-line notation",
            "generator": list(range(1, m)) + [0] if m > 1 else [0],
            "shifts": shifts,
        })
        projection_method = "cyclic shift exponent k modulo p"
    else:  # functions
        degree = int(object_dimension if object_dimension not in (None, "") else 3)
        if degree < 0:
            raise ValueError("polynomial degree must be >= 0")
        token = []
        for _ in range(dimension):
            coeffs = [rng.randrange(p) for _ in range(degree + 1)]
            if degree > 0 and coeffs[-1] == 0:
                coeffs[-1] = rng.randrange(1, p)
            token.append({
                "kind": "polynomial_function",
                "domain": f"F_{p}",
                "codomain": f"F_{p}",
                "variable": "x",
                "degree": degree,
                "coefficients": coeffs,
                "expression": _function_expression(coeffs, p),
            })
        metadata.update({"function_family": f"polynomials F_{p} -> F_{p}", "polynomial_degree": degree})
        projection_method = "function evaluation at x=1 modulo p"

    field_projection = [_project(value, token_type, p) for value in token]
    return {
        "dimension": dimension,
        "type": token_type,
        "seed": seed,
        "field": f"F_{p}",
        "parameters": metadata,
        "token": token,
        "field_projection": field_projection,
        "projection_method": projection_method,
        "warning": "The finite-field projection is an analysis representation and need not be injective for structured token types.",
    }
