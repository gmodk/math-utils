# Correlation & Regression Explorers

Four experiences, served by one local Python application:

- `correlation_geometry_interactive_explorer.html` — Correlation as Geometry.
- `explorer_6_multiple_regression_projection_subspace.html` — Multiple Regression as Projection onto a Subspace.
- `explorer_9_bias_variance_polynomial_complexity.html` — Bias–Variance Tradeoff and Polynomial Complexity.
- `explorer_11_bayesian_linear_regression_posterior_geometry.html` — Bayesian Linear Regression Posterior Geometry.

Start the complete platform from the root with `python launch.py --no-browser`; open `http://127.0.0.1:8004/`. Standalone: run this directory's `app.py` with the root shared environment; `HOST` defaults to `127.0.0.1`, `PORT` to `8004`. Direct `file://` opening is no longer supported: calculations require the local Python server.

## Architecture and API

`engines.py` owns sampling, statistics, linear algebra, and mathematical plot coordinates. `contracts.py` defines finite Pydantic inputs/outputs. `app.py` serves only registered pages, local assets and documentation. Six ES modules in `static/` handle controls, fetch cancellation/debouncing, DOM updates, SVG/Canvas rendering, and camera/pixel transforms. Assets and requests are constrained to the local origin. No build step or additional runtime dependencies.

- `GET /api/health` — ready status, engine version, four-explorer count.
- `GET /api/catalog` — exactly four IDs, titles, and page routes.
- `POST /api/v1/correlation/analyze` — `seed`, `rho`, `w`.
- `POST /api/v1/multiple-regression/analyze` — `seed`, `beta1`, `beta2`, `rho`, `sigma`, `n`.
- `POST /api/v1/bias-variance/analyze` — `seed`, `degree`, `sigma`, `n`, `x0`.
- `POST /api/v1/bayesian/analyze` — `seed`, `beta`, `sigma`, `tau`, `n`, `x0`.

Empty objects select source-declared defaults and seed 2026. Bounds match the source controls; integer fields are strict. Slider steps are preserved in HTML, not imposed as extra API restrictions. Invalid bounds, types, unknown fields and non-finite numbers return structured 422 errors. Singular/ill-conditioned systems also return a structured 422, without fabricated zero coefficients. Outputs retain full precision; only browser labels are rounded. `/openapi.json` describes the typed contracts; remote documentation assets are disabled.

## Reproducibility

Protocol: `sha256-pcg64-boxmuller-v1`. The request/response seed is an integer in `[0, 4294967295]`, default 2026. Stream state is the first 16 bytes, interpreted big-endian, of SHA-256 over ASCII `protocol:seed:stream-name`. Stream names are `correlation`, `multiple-regression`, `polynomial-sample`, `polynomial-monte-carlo`, and `bayesian`.

Each independent normal uses two nonzero uniform draws and the Box–Muller cosine transform. The sine variate is discarded, matching the source transform. Random generators are request-local. Identical parameters and seed reproduce all mathematical results in the same engine/numerical runtime. Cross-platform comparisons allow floating-point tolerances.

Resample increments the seed modulo 2³². Source data-generating controls in multiple regression, polynomial regression and Bayesian regression also advance it. Camera/highlight controls make no request. Correlation controls, degree/x₀, and Bayesian τ/x₀ retain the seed; redraws and retries retain it. Thus weight-only changes keep the scatter, and repeated Monte Carlo calculations at the same settings are stable. The original unseeded pages generated fresh scatter on correlation redraws and fresh Monte Carlo samples on every calculation; reproducibility intentionally changes those behaviors.

## Preserved conventions

- Correlation: 450 population-standardized Gaussian pairs, exact text thresholds, angle `acos(rho)`, 201-point two-asset variance curve, original variance-axis bounds.
- Multiple regression: centered two-predictor model, fitted intercept, Gram–Schmidt display coordinates, positive residual norm, residual orthogonality and SST/SSR/SSE decomposition. Determinant remains a scale-dependent indicator.
- Polynomial: `sin(pi*x)+0.4*x`, uniform x on `[-1,1)`, monomials including intercept, penalty `1e-7` on every coefficient, train MSE on the displayed data, noiseless test MSE over 160 endpoint-inclusive grid points, 80 Monte Carlo samples, variance denominator 79, 200-point display curves.
- Bayesian: true intercept 0.35; known noise; zero-centered isotropic prior on both coefficients; likelihood/OLS covariance; posterior mean/covariance; 161-point two-SD coefficient contours; beta marginal interval and 120-point predictive bounds at ±1.96 SD; 100-point ±2 SD bounds for plot scaling.

The Bayesian source declares noise default 0.8 with min 0.15 and step 0.02. Chromium normalizes this slider to **0.81**; the original attributes and browser behavior are preserved. API default remains the explicitly declared 0.8. The source's quick-reference wording about both coefficient intervals and shrinkage is retained, with an added clarification: only beta's interval and the OLS beta comparison are displayed. Coefficient ellipses are not 95% joint contours.

Solves use NumPy linear algebra rather than the original hand-written elimination. Condition numbers above `1e14` and degenerate response/predictor geometry are rejected. There is no tiny-pivot or zero-coefficient fallback. Tests compare coefficients against explicit normal equations and least-squares references.

## Visual and documentation preservation

Controls, ranges, steps, declared defaults, metric labels, plot IDs and quick-reference sections are checked against `tests/fixtures/regression-source-contract.json`. Styling uses local Math Utils navy/panel/accent variables, system controls, serif headings, and monospaced formulas. Plot colors, ticks and label placement are adjusted for readable dark surfaces. Mathematical data and source grids are preserved.

`MATHEMATICAL_THEORY.md` and `.docx` remain unchanged as historical references covering the former larger collection. They are not the current application catalog. The original four HTML snapshots remain in `backups/four-explorer-rebuild/` at the repository root pending browser approval.
