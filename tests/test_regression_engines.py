from pathlib import Path
import importlib.util
import math
import numpy as np
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'modules/regression_geometry_explorers'
spec = importlib.util.spec_from_file_location('regression_engines', MODULE / 'engines.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


@pytest.mark.parametrize('rho', [-.95, -.5, 0, .2, .95])
@pytest.mark.parametrize('w', [0, .5, 1])
def test_correlation(rho, w):
    result = engine.correlation(rho=rho, w=w)
    assert result['theta'] == pytest.approx(math.acos(rho), abs=1e-12)
    assert result['variance'] == pytest.approx(w*w+(1-w)**2+2*w*(1-w)*rho)
    points = np.asarray(result['scatter'])
    # 450 independent pairs: 0.12 is a documented finite-sample tolerance.
    assert np.corrcoef(points.T)[0, 1] == pytest.approx(rho, abs=.12)
    assert len(points) == 450 and len(result['variance_curve']) == 201


@pytest.mark.parametrize('rho', [-.95, .45, .95])
def test_multiple_regression(rho):
    result = engine.multiple_regression(rho=rho)
    x = np.column_stack([np.ones(len(result['y'])), result['x1'], result['x2']])
    e = np.asarray(result['residual'])
    assert np.allclose(x.T@e, 0, atol=1e-10)
    assert result['sst'] == pytest.approx(result['ssr']+result['sse'], rel=1e-12)
    assert result['r_squared'] == pytest.approx(math.cos(result['theta'])**2)
    reference = np.linalg.lstsq(x, result['y'], rcond=None)[0]
    assert np.allclose(result['coefficients'], reference, atol=1e-10)


def test_singular_and_constant_response():
    with pytest.raises(engine.NumericalError):
        engine.multiple_fit([1,2,3], [2,4,6], [2,3,4])
    with pytest.raises(engine.NumericalError):
        engine.multiple_fit([1,2,3,4], [1,4,2,5], [1,1,1,1])
    with pytest.raises(engine.NumericalError):
        engine.bayesian_fit(np.ones(10), np.arange(10), .8, 1, 0)


@pytest.mark.parametrize('degree,n', [(1,35),(4,35),(12,15),(12,100)])
def test_polynomial_reference_and_definitions(degree,n):
    r = engine.bias_variance(degree=degree,n=n)
    x,y=np.asarray(r['x']),np.asarray(r['y'])
    # Independent construction of source monomial normal equations.
    design=np.array([[xi**j for j in range(degree+1)] for xi in x])
    reference=np.linalg.solve(design.T@design+1e-7*np.eye(degree+1),design.T@y)
    assert np.allclose(r['coefficients'],reference,atol=1e-7,rtol=1e-6)
    fitted=design@np.asarray(r['coefficients'])
    assert r['train_mse']==pytest.approx(np.mean((y-fitted)**2),abs=1e-10)
    grid=np.asarray(r['test_grid'])
    assert len(grid)==160 and grid[0,0]==-1 and grid[-1,0]==1
    assert r['test_mse']==pytest.approx(np.mean((grid[:,1]-grid[:,2])**2))
    predictions=np.asarray(r['predictions'])
    assert len(predictions)==80
    assert r['bias_squared']==pytest.approx((predictions.mean()-(math.sin(math.pi*.6)+.4*.6))**2)
    assert r['variance']==pytest.approx(sum((predictions-predictions.mean())**2)/79)
    assert r['noise']==pytest.approx(.35**2)


@pytest.mark.parametrize('tau', [.15,1,5])
def test_bayesian_closed_form_and_contours(tau):
    r=engine.bayesian(tau=tau)
    x=np.column_stack([np.ones(len(r['x'])),r['x']]);y=np.asarray(r['y'])
    cov=np.asarray(r['covariance'])
    reference=np.linalg.inv(x.T@x/.8**2+np.eye(2)/tau**2)
    assert np.allclose(cov,reference,atol=1e-12)
    assert np.allclose(r['mean'],reference@x.T@y/.8**2,atol=1e-12)
    row=np.array([1,1.5])
    assert r['predictive_variance']==pytest.approx(.8**2+row@cov@row)
    for name, matrix, mean in [('prior',np.eye(2)*tau**2,np.zeros(2)),
                               ('likelihood',np.array(r['likelihood_covariance']),r['ols']),
                               ('posterior',cov,r['mean'])]:
        assert np.allclose(matrix,matrix.T) and np.all(np.linalg.eigvalsh(matrix)>0)
        delta=np.array(r['ellipses'][name])-mean
        contours=np.einsum('ij,jk,ik->i',delta,np.linalg.inv(matrix),delta)
        assert np.allclose(contours,4,atol=1e-9)


@pytest.mark.parametrize('name', ['correlation','multiple_regression','bias_variance','bayesian'])
def test_seed_reproducibility(name):
    function=getattr(engine,name)
    assert function(seed=123)==function(seed=123)
    assert function(seed=123)!=function(seed=124)


def test_retained_sample_controls():
    assert engine.correlation(w=.2)['scatter']==engine.correlation(w=.8)['scatter']
    assert engine.bias_variance(degree=2)['x']==engine.bias_variance(degree=8)['x']
    assert engine.bayesian(tau=.2)['y']==engine.bayesian(tau=3)['y']


@pytest.mark.parametrize('rho,label',[(-.8,'Moderate negative alignment'),(-.3,'Weak negative alignment'),
    (-.05,'Near orthogonality'),(.05,'Near orthogonality'),(.3,'Weak positive alignment'),(.8,'Moderate positive alignment')])
def test_interpretation_boundaries(rho,label):
    assert engine.interpretation(rho)==label
