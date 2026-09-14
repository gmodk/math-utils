# Mathematical Theory Behind the Statistical Geometry Explorers

## 1. Unifying viewpoint

The eleven explorers can be organized around one structural idea: many statistical constructions are linear-algebraic operations in an inner-product space.

For finite samples, vectors live in Euclidean spaces such as `R^n`. For random variables with finite second moments, centered variables live naturally in the Hilbert-space setting of `L²`. The recurring objects are:

- inner products and angles;
- Gram and covariance matrices;
- orthogonal projection;
- eigendecomposition and principal subspaces;
- quadratic forms;
- conditioning and inverse problems;
- constrained or penalized optimization;
- Gaussian posterior geometry.

This vocabulary connects correlation, PCA, portfolio theory, ordinary least squares, regularization, multicollinearity, bias–variance analysis, principal component regression and Bayesian regression.

## 2. Correlation as an angle

For random variables `X,Y` with finite nonzero variance, define centered versions

`X_c = X - E[X]`, `Y_c = Y - E[Y]`.

In `L²`, the inner product is

`<X_c,Y_c> = E[X_c Y_c] = Cov(X,Y)`.

The induced norm is

`||X_c|| = sqrt(Var(X)) = sigma_X`.

Therefore

`rho(X,Y) = <X_c,Y_c> / (||X_c|| ||Y_c||)`.

This has exactly the form of a cosine, so

`rho(X,Y) = cos(theta)`.

Cauchy–Schwarz immediately gives `|rho| <= 1`. Zero correlation corresponds to orthogonality after centering, not necessarily independence.

For standardized variables `Z_1,...,Z_p`, the correlation matrix is the Gram matrix

`R_ij = <Z_i,Z_j>`.

Hence every valid correlation matrix must be positive semidefinite. For three variables,

`R = [[1,r12,r13],[r12,1,r23],[r13,r23,1]]`

must satisfy

`det(R) = 1 + 2 r12 r13 r23 - r12² - r13² - r23² >= 0`.

Explorer 1 makes this Gram-matrix geometry explicit.

## 3. Covariance geometry and PCA

For a random vector `X in R^p` with mean `mu`, the covariance matrix is

`Sigma = E[(X-mu)(X-mu)^T]`.

It is symmetric positive semidefinite. A constant Mahalanobis-distance set satisfies

`(x-mu)^T Sigma^{-1} (x-mu) = c`

when `Sigma` is positive definite. In two dimensions this is an ellipse; in three dimensions it is an ellipsoid.

By the spectral theorem,

`Sigma = V Lambda V^T`,

where the columns of `V` are orthonormal eigenvectors and `Lambda=diag(lambda_1,...,lambda_p)` contains nonnegative eigenvalues.

In the eigenvector basis,

`(x-mu)^T Sigma^{-1} (x-mu) = sum_i z_i²/lambda_i`.

Thus ellipsoid semiaxis lengths are proportional to `sqrt(lambda_i)`. Principal component analysis is exactly this eigendecomposition:

- PC1 is the direction maximizing variance subject to unit norm;
- PC2 maximizes remaining variance subject to orthogonality to PC1;
- and so on.

The explained-variance ratio of PC `i` is

`lambda_i / sum_j lambda_j`.

Explorers 2 and 4 connect matrix eigendecomposition to observable point-cloud geometry.

## 4. Portfolio variance as a quadratic form

Let asset returns be collected in the random vector `R`, with covariance matrix `Sigma`, and let weights be `w`. Portfolio return is

`R_P = w^T R`.

Its variance is

`Var(R_P) = w^T Sigma w`.

Expanding,

`Var(R_P) = sum_i w_i² sigma_i² + 2 sum_{i<j} w_i w_j sigma_i sigma_j rho_ij`.

This is a quadratic form. For three long-only assets,

`w_1+w_2+w_3=1`, `w_i>=0`.

The feasible set is a two-dimensional simplex (a triangle). Mapping each feasible weight vector to `w^T Sigma w` creates a risk surface over the simplex.

Diversification is therefore geometric: negative or low covariance can create directions in weight space along which the quadratic form is smaller than the weighted average of individual risks.

Explorer 3 visualizes this surface.

## 5. Ordinary least squares as orthogonal projection

### Simple regression

Consider

`y_i = alpha + beta x_i + epsilon_i`.

After centering,

`y_c = beta x_c + e`.

Ordinary least squares minimizes

`||y_c - beta x_c||²`.

The minimizer satisfies

`beta_hat = <x_c,y_c>/<x_c,x_c>`.

Therefore

`y_hat_c = beta_hat x_c`

is the orthogonal projection of `y_c` onto `span(x_c)`.

The residual

`e = y_c - y_hat_c`

is orthogonal to the fitted subspace:

`<x_c,e> = 0`.

Because `y_hat_c` and `e` are orthogonal,

`||y_c||² = ||y_hat_c||² + ||e||²`.

Statistically,

`SST = SSR + SSE`.

The coefficient of determination is

`R² = SSR/SST = ||y_hat_c||²/||y_c||²`.

If `theta` is the angle between `x_c` and `y_c`, then in simple regression with intercept,

`R² = cos²(theta) = r²`.

Explorer 5 visualizes these identities.

### Multiple regression

Let `X_c` be the centered design matrix. OLS solves

`min_beta ||y_c-X_c beta||²`.

Differentiating gives the normal equations

`X_c^T X_c beta_hat = X_c^T y_c`.

When `X_c^T X_c` is invertible,

`beta_hat = (X_c^T X_c)^{-1} X_c^T y_c`.

Fitted values are

`y_hat_c = P_X y_c`

with projection matrix

`P_X = X_c (X_c^T X_c)^{-1} X_c^T`.

The matrix `P_X` is symmetric and idempotent:

`P_X^T=P_X`, `P_X²=P_X`.

Residuals satisfy

`X_c^T e = 0`.

Thus multiple regression is projection onto the column space of the design matrix. Explorer 6 renders the two-predictor case as projection onto a plane.

## 6. Regularization: ridge and lasso geometry

OLS may be unstable when the design matrix is ill-conditioned or when model complexity is high.

### Ridge regression

Ridge solves

`min_beta ||y-X beta||² + lambda ||beta||²_2`.

Its closed-form solution is

`beta_ridge = (X^T X + lambda I)^{-1} X^T y`.

The term `lambda I` shifts all eigenvalues of `X^T X` away from zero, stabilizing inversion.

Equivalent constrained form:

`min ||y-X beta||² subject to ||beta||_2 <= t`.

The constraint set is an `L²` ball: a circle in two coefficient dimensions.

### Lasso

Lasso solves

`min_beta ||y-X beta||² + lambda ||beta||_1`.

Equivalent constrained form:

`min ||y-X beta||² subject to ||beta||_1 <= t`.

The `L¹` ball is diamond-shaped in two dimensions. Its corners lie on coordinate axes, making exact zeros geometrically likely when loss contours first touch the constraint boundary.

Explorer 7 compares OLS, ridge and lasso in coefficient space.

## 7. Multicollinearity, VIF and conditioning

Multicollinearity occurs when columns of `X` are nearly linearly dependent. In the two-standardized-predictor case, the correlation matrix is

`R = [[1,rho],[rho,1]]`

with eigenvalues

`1+rho` and `1-rho` (ordered by magnitude depending on the sign).

As `|rho| -> 1`, one eigenvalue approaches zero and the matrix becomes nearly singular.

A spectral condition number for the design geometry is

`kappa(X) = sqrt(lambda_max(X^T X)/lambda_min(X^T X))`.

For the standardized two-predictor idealization,

`kappa = sqrt((1+|rho|)/(1-|rho|))`.

The variance of OLS coefficients is

`Var(beta_hat | X) = sigma² (X^T X)^{-1}`.

Small eigenvalues therefore imply large coefficient uncertainty.

For two predictors, the variance inflation factor is

`VIF = 1/(1-R_j²)`.

If each predictor is regressed on the other, `R_j²=rho²`, hence

`VIF = 1/(1-rho²)`.

Explorer 8 demonstrates the widening sampling distribution of coefficients as collinearity increases.

## 8. Bias–variance decomposition

Suppose

`Y = f(X) + epsilon`, `E[epsilon]=0`, `Var(epsilon)=sigma²`.

For a fitted predictor `f_hat(x)` obtained from a random training sample, the expected squared prediction error at a fixed `x` decomposes as

`E[(Y-f_hat(x))²] = Bias[f_hat(x)]² + Var[f_hat(x)] + sigma²`.

Here

`Bias[f_hat(x)] = E[f_hat(x)] - f(x)`.

Low-complexity models can have high bias and low variance. Highly flexible models can reduce bias but become sensitive to training-sample fluctuations, increasing variance.

Polynomial degree is a convenient complexity parameter because the model spaces are nested:

`P_1 subset P_2 subset ...`.

Explorer 9 estimates this decomposition numerically by repeated sampling.

## 9. Principal component regression

PCA transforms correlated predictors into orthogonal scores.

Let the centered design matrix have singular/eigen decomposition based on

`X^T X = V Lambda V^T`.

PC score matrix is

`Z = X V`.

Columns of `Z` are orthogonal in sample space.

PCR keeps the first `k` components:

`Z_k = X V_k`

and fits

`gamma_hat = (Z_k^T Z_k)^{-1} Z_k^T y`.

Coefficients in the original predictor coordinates are

`beta_PCR = V_k gamma_hat`.

PCR stabilizes regression by discarding low-variance directions, which are often poorly conditioned. But PCA is unsupervised: it chooses directions with large predictor variance, not directions with strongest relationship to `y`. A low-variance component can carry important predictive signal.

Explorer 10 is designed to reveal this distinction.

## 10. Bayesian linear regression and posterior geometry

Assume

`y | beta ~ N(X beta, sigma² I)`

and a Gaussian prior

`beta ~ N(m_0, S_0)`.

The posterior is Gaussian:

`S_n = (S_0^{-1} + X^T X/sigma²)^{-1}`

and

`m_n = S_n (S_0^{-1}m_0 + X^T y/sigma²)`.

For zero prior mean and isotropic prior covariance `S_0=tau² I`,

`S_n = (X^T X/sigma² + I/tau²)^{-1}`.

This formula exposes the relation to ridge regression: the posterior mean (or MAP under this Gaussian setup) has the same algebraic shrinkage structure as an `L²` penalty.

For a new row vector `x_*`, the posterior predictive distribution is

`y_* | x_*,D ~ N(x_*^T m_n, sigma² + x_*^T S_n x_*)`.

The predictive variance contains two terms:

1. observation noise `sigma²`;
2. parameter uncertainty `x_*^T S_n x_*`.

Explorer 11 visualizes the prior, likelihood and posterior as ellipses in coefficient space and displays the posterior predictive band.

## 11. One conceptual map

The eleven explorers are different manifestations of a compact set of structural operations.

### Inner products
Create covariance, correlation, angles and least-squares objectives.

### Gram matrices
Encode pairwise inner products. Correlation matrices and `X^T X` are Gram matrices.

### Orthogonal projection
Explains OLS fitted values, residual orthogonality and sum-of-squares decompositions.

### Spectral decomposition
Explains PCA, ellipsoids, condition numbers and PCR.

### Quadratic forms
Explain Mahalanobis distance, portfolio variance, OLS curvature and Gaussian log-likelihoods.

### Convex penalties
Modify the least-squares geometry to control estimator complexity.

### Probability on parameter space
Turns a single fitted coefficient vector into a posterior distribution with uncertainty geometry.

## 12. Limitations of the visualizations

These explorers intentionally compress mathematical objects into two or three display dimensions.

- A 3D covariance picture is exact only for three variables.
- Higher-dimensional PCA displays are projections onto selected PCs.
- Gaussian scatter and posterior ellipses rely on Gaussian assumptions.
- VIF is a local diagnostic for linear dependence and does not by itself diagnose every modeling problem.
- Low training error is not evidence of good generalization.
- PCR can discard predictive low-variance directions.
- Lasso solutions depend on scaling; practical lasso workflows standardize predictors.
- Bayesian credible intervals depend on the prior and likelihood assumptions.

## 13. Bibliography

- Axler, Sheldon. *Linear Algebra Done Right*. Springer.
- Strang, Gilbert. *Linear Algebra and Its Applications*. Cengage.
- Boyd, Stephen, and Lieven Vandenberghe. *Convex Optimization*. Cambridge University Press.
- Hastie, Trevor, Robert Tibshirani, and Jerome Friedman. *The Elements of Statistical Learning*. Springer.
- James, Gareth, Daniela Witten, Trevor Hastie, Robert Tibshirani, and Jonathan Taylor. *An Introduction to Statistical Learning*. Springer.
- Bishop, Christopher M. *Pattern Recognition and Machine Learning*. Springer.
- Gelman, Andrew, et al. *Bayesian Data Analysis*. CRC Press.
- Casella, George, and Roger L. Berger. *Statistical Inference*. Cengage.
