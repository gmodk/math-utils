"""Public finite JSON contracts; slider increments are presentation metadata."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

Number = Annotated[FiniteFloat, Field(strict=True)]
Vec2 = tuple[Number, Number]
Vec3 = tuple[Number, Number, Number]
Matrix2 = tuple[Vec2, Vec2]
Seed = Annotated[int, Field(strict=True, ge=0, le=4294967295)]


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Request(Model):
    seed: Seed = 2026


class CorrelationRequest(Request):
    rho: Annotated[Number, Field(ge=-.95, le=.95)] = .2
    w: Annotated[Number, Field(ge=0, le=1)] = .5


class MultipleRequest(Request):
    beta1: Annotated[Number, Field(ge=-2.5, le=2.5)] = 1.1
    beta2: Annotated[Number, Field(ge=-2.5, le=2.5)] = .7
    rho: Annotated[Number, Field(ge=-.95, le=.95)] = .45
    sigma: Annotated[Number, Field(ge=.05, le=2.5)] = .9
    n: Annotated[int, Field(strict=True, ge=20, le=400)] = 120


class BiasRequest(Request):
    degree: Annotated[int, Field(strict=True, ge=1, le=12)] = 4
    sigma: Annotated[Number, Field(ge=.05, le=1.2)] = .35
    n: Annotated[int, Field(strict=True, ge=15, le=100)] = 35
    x0: Annotated[Number, Field(ge=-1, le=1)] = .6


class BayesianRequest(Request):
    beta: Annotated[Number, Field(ge=-2.5, le=2.5)] = 1.2
    sigma: Annotated[Number, Field(ge=.15, le=2.5)] = .8
    tau: Annotated[Number, Field(ge=.15, le=5)] = 1
    n: Annotated[int, Field(strict=True, ge=10, le=250)] = 50
    x0: Annotated[Number, Field(ge=-3, le=3)] = 1.5


class Response(Model):
    seed: Seed
    engine_version: str
    seed_protocol: str


class CorrelationResponse(Response):
    theta: Number
    theta_degrees: Number
    variance: Number
    interpretation: str
    diversification: str
    scatter: Annotated[list[Vec2], Field(min_length=450,max_length=450)]
    vectors: tuple[Vec2,Vec2]
    angle_arc: list[Vec2]
    variance_curve: Annotated[list[Vec2], Field(min_length=201,max_length=201)]
    variance_bounds: Vec2


class Coordinates(Model):
    x1: Vec3
    x2: Vec3
    y: Vec3
    fitted: Vec3
    residual: Vec3


class MultipleResponse(Response):
    x1: list[Number]
    x2: list[Number]
    y: list[Number]
    means: Vec3
    centered: list[Vec2]
    centered_y: list[Number]
    gram: Matrix2
    coefficients: Vec3
    fitted: list[Number]
    residual: list[Number]
    sst: Number
    ssr: Number
    sse: Number
    ssr_plus_sse: Number
    r_squared: Number
    theta: Number
    theta_degrees: Number
    cos_squared: Number
    correlation: Number
    orthogonality: Vec2
    determinant: Number
    condition: Number
    coordinates: Coordinates


class BiasResponse(Response):
    x: list[Number]
    y: list[Number]
    coefficients: list[Number]
    condition: Number
    train_mse: Number
    test_mse: Number
    bias_squared: Number
    variance: Number
    noise: Number
    expected_error: Number
    predictions: Annotated[list[Number], Field(min_length=80,max_length=80)]
    test_grid: Annotated[list[Vec3], Field(min_length=160,max_length=160)]
    curve: Annotated[list[Vec3], Field(min_length=200,max_length=200)]


class Ellipses(Model):
    prior: list[Vec2]
    likelihood: list[Vec2]
    posterior: list[Vec2]


class BayesianResponse(Response):
    x: list[Number]
    y: list[Number]
    mean: Vec2
    covariance: Matrix2
    standard_deviations: Vec2
    beta_interval: Vec2
    ols: Vec2
    likelihood_covariance: Matrix2
    condition: Number
    predictive_variance: Number
    predictive_sd: Number
    ellipses: Ellipses
    ellipse_extent: Number
    predictive_bounds: Vec2
    curve: Annotated[list[tuple[Number,Number,Number,Number,Number]],Field(min_length=120,max_length=120)]


class Health(Model):
    status: Literal['ok'] = 'ok'
    engine_version: str
    explorers: int = 4


class Explorer(Model):
    id: str
    title: str
    path: str


CATALOG = [
    Explorer(id='correlation',title='Correlation as Geometry',path='/correlation_geometry_interactive_explorer.html'),
    Explorer(id='multiple-regression',title='Multiple Regression as Projection onto a Subspace',path='/explorer_6_multiple_regression_projection_subspace.html'),
    Explorer(id='bias-variance',title='Bias–Variance Tradeoff and Polynomial Complexity',path='/explorer_9_bias_variance_polynomial_complexity.html'),
    Explorer(id='bayesian',title='Bayesian Linear Regression Posterior Geometry',path='/explorer_11_bayesian_linear_regression_posterior_geometry.html'),
]
