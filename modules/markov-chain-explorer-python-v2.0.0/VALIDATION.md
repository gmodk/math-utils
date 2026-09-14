# Validation

Validated on 2026-09-14.

## Python runtime and API

- Python bytecode compilation: passed for `app.py`, `launch.py`, and the complete backend package.
- Automated tests: 11/11 passed.
- FastAPI health endpoint: returned `{"status":"ok","engine":"python"}`.
- FastAPI served the prebuilt HTML, CSS, JavaScript, and source map from the same local origin.
- The production JavaScript bundle calls `/api/analyze`, `/api/poisson`, and `/api/normalize`; Node.js is not used by the running application.

## Numerical invariants

The Python regression suite checks:

- every imported homogeneous transition row sums to one;
- the computed stationary distribution sums to one;
- cyclic Poisson-builder rows sum to one;
- Poissonized-kernel rows sum to one;
- expected hitting times satisfy `h_i = 1 + Σ_j P_ij h_j` outside the target set and vanish on the target;
- non-homogeneous kernels are multiplied in chronological order;
- a directed four-cycle is irreducible with period four;
- the thresholded four-cycle clique complex has Betti vector `(1,1,0)`;
- the non-homogeneous example yields three ordered transition slices;
- API analysis, Poisson generation, and selected-slice normalization return valid responses.

## Interactive 3D runtime

The shipped bundle was verified to contain a real Three.js WebGL renderer, a `markov-hypergraph-3d` canvas, orbit rotation, zoom-to-cursor and touch zoom, right-button panning, raycast selection, and draggable state meshes. The source and runtime bundle are both included.

The available cloud browser is isolated from localhost, so an end-to-end synthetic mouse-gesture run against the local server could not be performed in this environment. This is the only unverified item; the interaction code is compiled into the delivered runtime and its required markers are protected by an automated artifact test.

## Packaging

The deliverable excludes `.venv`, dependency directories, caches, Git metadata, legacy Sites infrastructure, and temporary build files. ZIP integrity, file inventory, and SHA-256 are checked after creation.
