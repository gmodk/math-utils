# Regression, Correlation & Statistical Geometry Explorers

A self-contained collection of eleven interactive HTML explorers for learning the geometry behind correlation, covariance, PCA, portfolio variance, ordinary least squares, regularization, multicollinearity, bias–variance tradeoffs, principal component regression, and Bayesian linear regression.

No server, build system, external JavaScript package, or network connection is required. Open `index.html` in a modern browser.

## Explorers

| # | Explorer | Main mathematical idea |
|---|---|---|
| 1 | 3D Correlation Vectors | A correlation matrix is a Gram matrix of unit vectors; correlations are cosines of angles. |
| 2 | Covariance Ellipsoid & PCA | Eigenvectors give principal axes; eigenvalues give variance along those axes. |
| 3 | 3-Asset Portfolio Variance Surface | Portfolio risk is the quadratic form `wᵀΣw` over the weight simplex. |
| 4 | Trivariate Scatter & PCA | Raw observations, covariance geometry and PCA are different views of the same structure. |
| 5 | Simple Regression / Projection Geometry | OLS is orthogonal projection of `y_c` onto `span(x_c)`. |
| 6 | Multiple Regression / Projection Subspace | OLS projects `y_c` onto the column space of the centered design matrix. |
| 7 | Ridge / Lasso Geometry | Regularization trades data fit against coefficient size; L2 and L1 penalties create different shrinkage geometry. |
| 8 | Multicollinearity / VIF / Condition Geometry | Near-linear dependence inflates coefficient variance and makes `XᵀX` ill-conditioned. |
| 9 | Bias–Variance / Polynomial Complexity | Prediction error decomposes into squared bias, estimator variance and irreducible noise. |
| 10 | Principal Component Regression | Rotate predictors into orthogonal PCs, retain selected components, then regress in score space. |
| 11 | Bayesian Linear Regression | Gaussian prior × Gaussian likelihood gives a Gaussian posterior and predictive distribution. |

Every explorer contains a **Quick reference guide** at the bottom explaining:
- each control or option;
- each chart;
- each metric;
- the central mathematical identity being visualized.

## Running locally

### Simplest method

Open:

```text
index.html
```

in Chrome, Firefox, Safari, Edge, or another current browser.

### Optional local HTTP server

From this directory:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

This is optional; all explorers are designed to run directly from the filesystem.

## Repository structure

```text
.
├── index.html
├── explorer_1_correlation_vectors_3d.html
├── explorer_2_covariance_ellipsoid_pca_3d.html
├── explorer_3_portfolio_variance_surface_3asset.html
├── explorer_4_trivariate_scatter_pca_3d.html
├── explorer_5_regression_projection_geometry.html
├── explorer_6_multiple_regression_projection_subspace.html
├── explorer_7_ridge_lasso_regularization_geometry.html
├── explorer_8_multicollinearity_vif_condition_geometry.html
├── explorer_9_bias_variance_polynomial_complexity.html
├── explorer_10_principal_component_regression.html
├── explorer_11_bayesian_linear_regression_posterior_geometry.html
├── MATHEMATICAL_THEORY.md
├── MATHEMATICAL_THEORY.docx
└── README.md
```

## Mathematical progression

The sequence is deliberate:

1. **Correlation becomes geometry.** Centered square-integrable random variables behave like vectors; correlation is a normalized inner product.
2. **Covariance becomes shape.** A covariance matrix determines an ellipsoid; PCA diagonalizes that geometry.
3. **Portfolio risk becomes a quadratic surface.** Asset covariance is converted into portfolio variance by `wᵀΣw`.
4. **Regression becomes projection.** Least squares is an orthogonal projection onto a model subspace.
5. **Regularization modifies projection.** Ridge and lasso trade projection accuracy against coefficient complexity.
6. **Multicollinearity exposes conditioning.** Nearly dependent predictors make inverse problems unstable.
7. **Model complexity creates bias–variance tradeoffs.**
8. **PCR uses spectral truncation** to stabilize a regression problem.
9. **Bayesian regression replaces a single optimum with a posterior geometry.**

The common language is linear algebra: inner products, Gram matrices, orthogonal projections, eigendecompositions, quadratic forms, conditioning and Gaussian geometry.

## Important modeling notes

The explorers are pedagogical rather than production analytics tools.

- Synthetic data are generated in-browser.
- Numerical solvers are intentionally small and transparent.
- The lasso implementation uses coordinate descent for the two-predictor centered problem.
- The minimum-variance portfolio in Explorer 3 is a grid-search approximation.
- Monte Carlo estimates in Explorers 8 and 9 vary from run to run.
- Gaussian assumptions in Explorers 4 and 11 are explicit modeling choices, not universal properties of financial or real-world data.
- PCA maximizes predictor variance, not predictive relevance; Explorer 10 is designed to make that distinction visible.

## Theory document

`MATHEMATICAL_THEORY.docx` is the polished document version.  
`MATHEMATICAL_THEORY.md` is included for repository-native reading and version control.

## Suggested learning route

For a first pass:

```text
1 → 2 → 5 → 6 → 8 → 7 → 9 → 10 → 11
```

For portfolio applications:

```text
1 → 2 → 4 → 3 → 10 → 11
```

## Technical design

The explorers intentionally use:
- vanilla HTML;
- vanilla JavaScript;
- HTML Canvas;
- no third-party dependencies;
- no network requests.

This keeps each file portable and inspectable.

## References

See `MATHEMATICAL_THEORY.md` / `.docx` for a compact bibliography. Core references include:
- Axler, *Linear Algebra Done Right*.
- Strang, *Linear Algebra and Its Applications*.
- Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*.
- James, Witten, Hastie & Tibshirani, *An Introduction to Statistical Learning*.
- Bishop, *Pattern Recognition and Machine Learning*.
- Gelman et al., *Bayesian Data Analysis*.
- Boyd & Vandenberghe, *Convex Optimization*.
