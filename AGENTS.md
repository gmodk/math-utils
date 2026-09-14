Math Utils repository instructions
Project purpose

Math Utils is a unified local platform that gathers several existing mathematical explorers behind one landing page and one Python launcher.

Non-negotiable preservation rule

Treat everything under modules/ as vendored, immutable applications.

Do not redesign, refactor, rename, reorganize, translate, simplify, or rewrite their interfaces, mathematical engines, APIs, routes, static assets, examples, documentation, or behavior.

If integration appears to require editing a module, stop and explain the conflict before changing it.

Included applications
modules/distributed-memory-architecture-atlas
Distributed Memory Architecture Atlas 2.1.
Includes the combinatorial, spectral-hypergraph, probabilistic, sheaf-theoretic, and information-theoretic approaches.
Preserve its geometry, graph/TDA, recovery, diagnostics, cryptography, and token-generation laboratories.
modules/markov-chain-explorer-python-v2.0.0
Python FastAPI numerical backend.
Prebuilt JavaScript/Three.js interface.
Preserve homogeneous and non-homogeneous chains, Poisson generation, CSV import, probability calculations, topology, layouts, and interactive 2D/3D hypergraphs.
Node.js must not be required at runtime.
modules/s_n_explorer_web
Python group-theory engine with its existing HTML/CSS/JavaScript interface.
Preserve permutations, cycles, composition, inverses, orders, signs, Cayley tables, dihedral groups, subgroups, normality, quotient groups, and conjugacy classes.
modules/regression_geometry_explorers
Preserve all eleven standalone correlation, covariance, PCA, regression, regularization, portfolio, multicollinearity, bias–variance, PCR, and Bayesian explorers.
Integration architecture

Keep the applications isolated on separate processes and ports:

Landing page: 8000
Distributed Memory Architecture Atlas: 8001
Markov Chain Explorer: 8002
S_n Explorer WebUI: 8003
Correlation and Regression Explorers: 8004

The root launch.py must:

Create and reuse one shared .venv.
Install root runtime requirements only when necessary.
Start all four applications.
Serve the landing page.
Report module readiness.
Open the browser unless --no-browser is supplied.
Accept --host and --port.
Shut down every child process cleanly.
Detect occupied ports before starting.

Do not combine module APIs under one route prefix because their root-relative assets and endpoints must remain untouched.

Landing page

The landing page is the only interface that may be independently redesigned.

It must provide direct access to all four applications and display their readiness. Do not embed or reproduce the module interfaces inside the landing page.

Validation requirements

Before completing any integration change:

Run the root integration tests.
Run the Atlas tests.
Run the Markov tests.
Run the S_n tests.
Compile-check all Python files.
Syntax-check the relevant JavaScript files.
Start the complete platform and verify HTTP 200 responses from the landing page and every module.
Confirm that all four readiness states are true.
Confirm that no retained file under modules/ changed unless the user explicitly authorized it.
Remove .venv, node_modules, caches, compiled Python files, Git metadata, and temporary files from release archives.
Documentation and delivery

Update README.md, CHANGELOG.md, and VALIDATION.md whenever integration behavior changes.

A completed delivery must include a clean ZIP archive, its byte size, SHA-256 checksum, validation results, and exact startup instructions.

Do not stop after planning. Implement, test, validate, and package the requested result.