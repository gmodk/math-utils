# S_n Explorer Web

A browser-based extension of the command-line **Symmetric Group Explorer** in `danielsfrede/python_projects`.

The mathematical engine remains Python. The GUI is a real HTML/CSS/JavaScript client served by a small dependency-free Python HTTP server, so the project requires no web framework and no JavaScript build step.

## Why this architecture

The original CLI already separates interaction (`main.py`) from group-theory logic (`symmetric_group.py`). Rewriting the algorithms in JavaScript would duplicate the mathematical source of truth. This version therefore uses:

- **Python** for permutations, composition, inverses, cycle structure, order, sign, Cayley tables, dihedral groups, subgroup closure, normality, quotient groups, and conjugacy classes.
- **HTML/CSS** for the browser interface.
- **Vanilla JavaScript** only for interaction, API calls, pagination, and SVG rendering.
- Python's standard-library `ThreadingHTTPServer` as the local web server.

## Interface design

The UI is rebuilt around the generated dark mathematical-workbench reference: fixed left navigation, serif mathematical typography, blue-gray borders, five invariant cards, a live overview table, a permutation detail inspector, and an SVG cycle graph. The overview is fully interactive: selecting a permutation updates both its structural data and the directed mapping visualization. The same visual system is used across the Cayley, dihedral, subgroup, quotient, and conjugacy views.

## Features

- Browse `S_n` for `1 <= n <= 8` with pagination, search and filters.
- Inspect each permutation in one-line and cycle notation.
- Compute inverse, order, parity, cycle type and self-inverse status.
- Compose `sigma o tau` using the original convention: apply `tau` first, then `sigma`.
- Render Cayley tables for `n <= 4`.
- Construct `D_m <= S_m` for `3 <= m <= 24` and render the regular polygon as SVG.
- Generate a subgroup from chosen permutation indices for `n <= 7`.
- Enumerate all subgroups of `S_n` and test normality for `n <= 4`.
- Build quotient groups `S_n / H` for normal subgroups, including cosets, element orders and the quotient Cayley table.
- Classify conjugacy classes of `S_n` by cycle type.

## Run

```bash
cd s_n_explorer_web
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

No `pip install` step is required.

Optional environment variables:

```bash
HOST=0.0.0.0 PORT=8080 python app.py
```

## Tests

If `pytest` is available:

```bash
pytest -q
```

The tests check composition convention, inverses, element orders and signs, the subgroup lattice size of `S_3`, normal subgroups of `S_3`, the quotient `S_3/A_3`, Cayley-table Latin-square structure, a defining dihedral relation, and `S_3` conjugacy-class sizes.

## Computational limits

These are mathematical/computational guardrails rather than arbitrary UI restrictions.

- `|S_n| = n!`, so full enumeration has factorial growth.
- A Cayley table contains `(n!)^2` entries.
- Exhaustive subgroup enumeration is exponential in the ambient group size in the worst case.

For that reason this UI allows broad browsing through `S_8`, but caps Cayley tables and exhaustive subgroup enumeration at `S_4`. Generated-subgroup closure remains available through `S_7`.

## Project structure

```text
s_n_explorer_web/
├── app.py                  # local HTTP server + JSON API
├── symmetric_group.py      # mathematical engine
├── static/
│   ├── index.html          # browser application
│   ├── styles.css          # responsive visual design
│   └── app.js              # interactions + SVG rendering
├── tests/
│   └── test_engine.py
├── PROJECT_ANALYSIS.md
└── README.md
```
