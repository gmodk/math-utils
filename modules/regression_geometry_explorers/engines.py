"""Deterministic statistical engines. All returned geometry uses mathematical coordinates."""
from __future__ import annotations

import hashlib
import math
import numpy as np

VERSION = "1.0.1"
PROTOCOL = "sha256-pcg64-boxmuller-v1"


class NumericalError(ValueError):
    pass


def rng(seed, stream):
    digest = hashlib.sha256(f"{PROTOCOL}:{seed}:{stream}".encode("ascii")).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest[:16], "big")))


def normal(generator):
    u, v = 0.0, 0.0
    while u == 0:
        u = generator.random()
    while v == 0:
        v = generator.random()
    return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


def checked_solve(a, b):
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise NumericalError("The linear system contains non-finite values.")
    try:
        condition = float(np.linalg.cond(a))
        if not math.isfinite(condition) or condition > 1e14:
            raise NumericalError("The design is singular or too ill-conditioned to solve reliably.")
        result = np.linalg.solve(a, b)
    except np.linalg.LinAlgError as exc:
        raise NumericalError("The linear system could not be solved.") from exc
    if not np.all(np.isfinite(result)):
        raise NumericalError("The calculation produced a non-finite result.")
    return result, condition


def envelope(seed, **values):
    return dict(seed=seed, engine_version=VERSION, seed_protocol=PROTOCOL, **values)


def interpretation(rho):
    if rho > .8: return "Strong positive alignment"
    if rho > .3: return "Moderate positive alignment"
    if rho > .05: return "Weak positive alignment"
    if rho >= -.05: return "Near orthogonality"
    if rho >= -.3: return "Weak negative alignment"
    if rho >= -.8: return "Moderate negative alignment"
    return "Strong negative alignment"


def diversification(rho):
    if rho < -.5: return "Strong cancellation potential"
    if rho < 0: return "Negative correlation helps hedging"
    if rho < .4: return "Some diversification benefit"
    if rho < .8: return "Limited diversification"
    return "Little diversification: assets move together"


def correlation(seed=2026, rho=.2, w=.5):
    generator = rng(seed, "correlation")
    s = math.sqrt(1-rho*rho)
    points = []
    for _ in range(450):
        z1, z2 = normal(generator), normal(generator)
        points.append([z1, rho*z1+s*z2])
    weights = np.linspace(0, 1, 201)
    variance = lambda weight: weight*weight+(1-weight)**2+2*weight*(1-weight)*rho
    theta = math.acos(rho)
    # Source's asymmetric vertical bounds are deliberate display conventions.
    ymin = min(0, variance(.5)-.1) if rho >= 0 else max(0, variance(.5)-.05)
    arc = [[.41*math.cos(t), .41*math.sin(t)] for t in np.linspace(0, theta, 65)]
    return envelope(seed, theta=theta, theta_degrees=math.degrees(theta),
                    variance=variance(w), interpretation=interpretation(rho),
                    diversification=diversification(rho), scatter=points,
                    vectors=[[1.,0.],[rho,s]], angle_arc=arc,
                    variance_curve=np.column_stack([weights,variance(weights)]).tolist(),
                    variance_bounds=[ymin,1.05])


def multiple_fit(x1, x2, y):
    x1,x2,y = (np.asarray(v,dtype=float) for v in (x1,x2,y))
    means = [float(x1.mean()),float(x2.mean()),float(y.mean())]
    xc = np.column_stack([x1-means[0],x2-means[1]])
    yc = y-means[2]
    gram = xc.T@xc
    coef, condition = checked_solve(gram,xc.T@yc)
    alpha = means[2]-coef@means[:2]
    fitted = alpha+np.column_stack([x1,x2])@coef
    residual = y-fitted
    fitted_centered = fitted-fitted.mean()
    sst,ssr,sse = float(yc@yc),float(fitted_centered@fitted_centered),float(residual@residual)
    # SST has squared response units; machine epsilon is not a zero-variance
    # threshold. A nonconstant response can legitimately have SST below epsilon.
    if not math.isfinite(sst) or sst <= 0:
        raise NumericalError("The response has no variation; R-squared and the subspace angle are undefined.")
    r2=ssr/sst
    theta=math.acos(float(np.clip(math.sqrt(max(0,r2)),-1,1)))
    u1=xc[:,0]/np.linalg.norm(xc[:,0])
    coeff=float(xc[:,1]@u1)
    orth=xc[:,1]-coeff*u1
    n2=float(np.linalg.norm(orth))
    if n2 <= 1e-10: raise NumericalError("The predictor plane is degenerate.")
    u2=orth/n2
    a,b,c=float(yc@u1),float(yc@u2),math.sqrt(sse)
    return dict(x1=x1.tolist(),x2=x2.tolist(),y=y.tolist(),means=means,
                centered=xc.tolist(),centered_y=yc.tolist(),gram=gram.tolist(),
                coefficients=[float(alpha),*coef.tolist()],fitted=fitted.tolist(),
                residual=residual.tolist(),sst=sst,ssr=ssr,sse=sse,ssr_plus_sse=ssr+sse,r_squared=r2,
                theta=theta,theta_degrees=math.degrees(theta),cos_squared=math.cos(theta)**2,
                correlation=float(gram[0,1]/math.sqrt(gram[0,0]*gram[1,1])),
                orthogonality=(xc.T@residual).tolist(),determinant=float(np.linalg.det(gram)),
                condition=condition,coordinates=dict(x1=[math.sqrt(gram[0,0]),0.,0.],
                x2=[coeff,n2,0.],y=[a,b,c],fitted=[a,b,0.],residual=[0.,0.,c]))


def multiple_regression(seed=2026,beta1=1.1,beta2=.7,rho=.45,sigma=.9,n=120):
    generator=rng(seed,"multiple-regression")
    rows=[]
    for _ in range(n):
        z1,z2,eps=normal(generator),normal(generator),normal(generator)
        x2=rho*z1+math.sqrt(1-rho*rho)*z2
        rows.append([z1,x2,beta1*z1+beta2*x2+sigma*eps])
    return envelope(seed,**multiple_fit(*np.asarray(rows).T))


def truth(x):
    return np.sin(np.pi*x)+.4*x


def polynomial_fit(x,y,degree):
    features=np.polynomial.polynomial.polyvander(x,degree)
    # Source applies 1e-7 to ALL coefficients, including the intercept.
    coef,condition=checked_solve(features.T@features+1e-7*np.eye(degree+1),features.T@y)
    return coef,condition


def polynomial_data(generator,n,sigma):
    x,y=[],[]
    for _ in range(n):
        xi=-1+2*generator.random()
        x.append(xi); y.append(float(truth(xi))+sigma*normal(generator))
    return np.asarray(x),np.asarray(y)


def bias_variance(seed=2026,degree=4,sigma=.35,n=35,x0=.6):
    x,y=polynomial_data(rng(seed,"polynomial-sample"),n,sigma)
    coef,condition=polynomial_fit(x,y,degree)
    predict=lambda xx: np.polynomial.polynomial.polyval(xx,coef)
    train=float(np.mean((y-predict(x))**2))
    test_x=np.linspace(-1,1,160)
    test=float(np.mean((predict(test_x)-truth(test_x))**2))
    generator=rng(seed,"polynomial-monte-carlo")
    predictions=[]
    for _ in range(80):
        xx,yy=polynomial_data(generator,n,sigma)
        cc,_=polynomial_fit(xx,yy,degree)
        predictions.append(float(np.polynomial.polynomial.polyval(x0,cc)))
    bias=float((np.mean(predictions)-truth(x0))**2)
    variance=float(np.var(predictions,ddof=1))
    grid=np.linspace(-1,1,200)
    return envelope(seed,x=x.tolist(),y=y.tolist(),coefficients=coef.tolist(),condition=condition,
                    train_mse=train,test_mse=test,bias_squared=bias,variance=variance,noise=sigma*sigma,
                    expected_error=bias+variance+sigma*sigma,predictions=predictions,
                    test_grid=np.column_stack([test_x,truth(test_x),predict(test_x)]).tolist(),
                    curve=np.column_stack([grid,truth(grid),predict(grid)]).tolist())


def ellipse(cov,mu):
    cov=np.asarray(cov,dtype=float)
    mu=np.asarray(mu,dtype=float)
    if (cov.shape!=(2,2) or mu.shape!=(2,) or not np.all(np.isfinite(cov))
            or not np.all(np.isfinite(mu)) or not np.array_equal(cov,cov.T)):
        raise NumericalError("A coefficient contour requires a finite symmetric 2x2 covariance.")
    try:
        values,vectors=np.linalg.eigh(cov)
    except np.linalg.LinAlgError as exc:
        raise NumericalError("The covariance eigensystem could not be computed.") from exc
    if values[0]<=0 or values[1]/values[0]>1e14:
        raise NumericalError("The covariance is not positive definite or is too ill-conditioned.")
    l2,l1=values
    v=vectors[:,1]
    # Deterministic orientation; geometry is independent of eigenvector signs.
    if v[1]<0 or (v[1]==0 and v[0]<0):v=-v
    v2=np.array([-v[1],v[0]])
    t=np.linspace(0,2*np.pi,161)
    return (mu+2*math.sqrt(l1)*np.cos(t)[:,None]*v+2*math.sqrt(l2)*np.sin(t)[:,None]*v2).tolist()


def bayesian_fit(x,y,sigma,tau,x0):
    design=np.column_stack([np.ones(len(x)),x])
    gram=design.T@design
    precision=gram/sigma**2+np.eye(2)/tau**2
    covariance,condition=checked_solve(precision,np.eye(2))
    covariance=(covariance+covariance.T)/2
    mu=covariance@(design.T@y/sigma**2)
    ols,_=checked_solve(gram,design.T@y)
    like,_=checked_solve(gram/sigma**2,np.eye(2))
    like=(like+like.T)/2
    def prediction(grid):
        rows=np.column_stack([np.ones(len(grid)),grid])
        mean=rows@mu
        variance=sigma**2+np.einsum('ij,jk,ik->i',rows,covariance,rows)
        return mean,variance
    grid=np.linspace(-3,3,120)
    mean,var=prediction(grid);sd=np.sqrt(var)
    scale_grid=np.linspace(-3,3,100)
    scale_mean,scale_var=prediction(scale_grid)
    extrema=np.concatenate([y,scale_mean+2*np.sqrt(scale_var),scale_mean-2*np.sqrt(scale_var)])
    pad=.1*float(np.ptp(extrema))
    _,pvar=prediction(np.array([x0]))
    sds=np.sqrt(np.diag(covariance))
    extent=max(2.5,*np.abs(mu),*np.abs(ols),2*tau)*1.2
    return dict(x=np.asarray(x).tolist(),y=np.asarray(y).tolist(),mean=mu.tolist(),covariance=covariance.tolist(),
                standard_deviations=sds.tolist(),beta_interval=[float(mu[1]-1.96*sds[1]),float(mu[1]+1.96*sds[1])],
                ols=ols.tolist(),likelihood_covariance=like.tolist(),condition=condition,
                predictive_variance=float(pvar[0]),predictive_sd=math.sqrt(pvar[0]),
                ellipses=dict(prior=ellipse(np.eye(2)*tau*tau,np.zeros(2)),
                              likelihood=ellipse(like,ols),posterior=ellipse(covariance,mu)),
                ellipse_extent=float(extent),predictive_bounds=[float(extrema.min()-pad),float(extrema.max()+pad)],
                curve=np.column_stack([grid,mean,mean-1.96*sd,mean+1.96*sd,var]).tolist())


def bayesian(seed=2026,beta=1.2,sigma=.8,tau=1.,n=50,x0=1.5):
    generator=rng(seed,"bayesian")
    rows=[]
    for _ in range(n):
        x=normal(generator);rows.append([x,.35+beta*x+sigma*normal(generator)])
    x,y=np.asarray(rows).T
    return envelope(seed,**bayesian_fit(x,y,sigma,tau,x0))
