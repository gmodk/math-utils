# Universal CSV Importer adaptation

| Universal importer capability | Markov-chain adaptation |
| --- | --- |
| Stable node ids and typed edges | Stable state ids; transition rows retain relation, time, confidence, count, enabled state, and metadata. |
| Reviewed CSV mapping | Auto-detected Markov schema with manual mapping and preview counts. |
| Cancel-safe snapshot replacement | The active chain is replaced only after structural and stochastic validation passes. |
| Multiple delimiters and quoted/multiline values | Preserved. |
| Category/relation toggles | State-category and transition-relation visibility filters. |
| 2D/3D graph | Interactive SVG 2D and WebGL 3D stochastic hypergraphs; the 3D camera supports orbit rotation, zoom, and pan. |
| Adaptive labels | Preserved, with probability-scaled state cores. |
| Exponential zoom | Preserved over the full 2% to 1,000,000% range. |
| Named projects and camera persistence | Local snapshots retain project, camera, positions, layout, filtration, Bayesian, and Poisson settings. |
| JSON/PNG export | Preserved; canonical Markov CSV export is added. |
| SCC/prerequisite analysis | Communicating classes, closed classes, transient/recurrent decomposition, periods, and absorption. |
| Spectral geometry and diffusion | Laplacian layout, stationary law, ordered transition products, evolution, contraction, and reversibilized gap. |
| GF(2) homology | Clique filtration of the thresholded transition support with β₀, β₁, and β₂. |
| Forman curvature | Weighted transition-support curvature. |
| Bayesian confidence | Dirichlet pseudocount smoothing from observed transition counts. |
| Robustness | Row-stochastic residual and worst single-edge dropout stationary shift. |
| Temporal readiness | Time-slice completeness and maximum row variation for non-homogeneous chains. |
| Pluggable analysis boundary | The browser sends typed project snapshots to a local Python API; numerical methods can be extended without changing the visual shell. |
