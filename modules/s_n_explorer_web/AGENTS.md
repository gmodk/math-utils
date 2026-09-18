# Sₙ Explorer integration rules

- The Python backend owns all group-theory calculations.
- The browser UI uses vanilla HTML, CSS, and JavaScript. Do not add Node.js, npm, a bundler, or a JavaScript framework.
- Preserve all existing routes, payload fields, controls, layouts, and mathematical conventions.
- Composition means sigma after tau: (sigma ∘ tau)(i) = sigma(tau(i)).
- API permutation arrays are zero-based internally; user-facing labels and trace values are one-based.
- Treat the current Math Utils module as authoritative for every feature unrelated to the composition animation.
- In particular, do not remove or regress any dihedral 2D/3D visualization, polygon choice, label mode, or transformation animation.
- Prefer additive, backward-compatible API changes.
- Run focused module tests and the full Math Utils test suite before finishing.