"""Reviewable migration helper; source snapshots beside this file remain unchanged."""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'modules/regression_geometry_explorers'
PAGES=[('correlation','correlation_geometry_interactive_explorer.html','Correlation'),
       ('multiple-regression','explorer_6_multiple_regression_projection_subspace.html','Multiple regression'),
       ('bias-variance','explorer_9_bias_variance_polynomial_complexity.html','Bias–variance'),
       ('bayesian','explorer_11_bayesian_linear_regression_posterior_geometry.html','Bayesian regression')]
engine=sys.argv[1]
filename=next(p[1] for p in PAGES if p[0]==engine)
source=(Path(__file__).parent/filename).read_text(encoding='utf-8')
source=re.sub(r'<script\b[^>]*>.*?</script>','',source,flags=re.S|re.I)
source=re.sub(r'<style\b[^>]*>.*?</style>','',source,flags=re.S|re.I)
source=source.replace('</head>','<link rel="icon" href="/static/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/static/styles.css"></head>')
nav=''.join(f'<a href="/{f}"'+(' aria-current="page"' if e==engine else '')+f'>{label}</a>' for e,f,label in PAGES)
bar='<header class="topbar"><a class="brand" href="/">Statistical Geometry<small>Math Utils · four explorations</small></a><nav aria-label="Explorers">'+nav+'</nav></header>'
status='<div class="request-state" role="status" aria-live="polite"><span id="request-message">Loading calculations…</span><strong>Sample seed <span id="seed-value">2026</span></strong><button id="retry" hidden>Retry</button></div>'
source=re.sub(r'<body[^>]*>',f'<body data-engine="{engine}">'+bar+'<main>'+status,source,count=1)
source=source.replace('</body>','</main><script type="module" src="/static/api.js"></script></body>')
# Associate the source's labels without changing control attributes.
source=re.sub(r'<label>(.*?)</label>(\s*<input id="([^"]+)")',lambda m:f'<label for="{m[3]}">{m[1]}</label>{m[2]}',source)
source=re.sub(r'<canvas\b([^>]*)>',lambda m:'<canvas role="img"'+m[1]+('' if 'aria-label=' in m[1] else ' aria-label="'+re.search(r'id="([^"]+)"',m[1])[1]+' visualization"')+'>',source)
source=source.replace('Explorer 6 — Multiple Regression as Projection onto a Plane / Subspace','Multiple Regression as Projection onto a Subspace')
source=source.replace('Explorer 9 — Bias–Variance Tradeoff &amp; Polynomial Complexity','Bias–Variance Tradeoff and Polynomial Complexity').replace('Explorer 9 — Bias–Variance Tradeoff & Polynomial Complexity','Bias–Variance Tradeoff and Polynomial Complexity')
source=source.replace('Explorer 11 — Bayesian Linear Regression & Posterior Geometry','Bayesian Linear Regression Posterior Geometry')
notes={
 'correlation':'The scatter is a finite sample from population-standardized variables. Reusing a seed keeps the same underlying sample on redraws; the displayed correlation is the population parameter.',
 'multiple-regression':'The determinant is a scale-dependent indicator, not a condition number. Singular designs produce an explicit error. Camera and highlight changes reuse the current calculation.',
 'bias-variance':'The solver retains the source’s 10⁻⁷ penalty on every coefficient, including the intercept. Variance uses 80 simulations and denominator 79. Reusing a seed makes the Monte Carlo estimate repeatable.',
 'bayesian':'Coefficient ellipses have Mahalanobis radius 2; they are not 95% joint credible regions. The displayed interval is for β only, and OLS β provides the shrinkage comparison. Predictive limits use 1.96 SD. The source declares σ=0.80 on a step lattice starting at 0.15; browsers may normalize that initial slider value.'}
source=source.replace('</main>',f'<aside class="migration-note">{notes[engine]}</aside></main>')
(DEST/filename).write_text(source,encoding='utf-8')
