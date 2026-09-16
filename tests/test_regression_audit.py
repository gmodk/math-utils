"""Independent scalar references transcribed from the four preserved HTML sources.

The only addition to the source generators is the documented deterministic stream
protocol. References deliberately do not call the production engine math helpers.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import math
import numpy as np
import pytest
from test_regression_engines import engine
from test_regression_api import client, module


def source_rng(seed, stream):
    message=f'sha256-pcg64-boxmuller-v1:{seed}:{stream}'.encode('ascii')
    state=int.from_bytes(hashlib.sha256(message).digest()[:16], 'big')
    return np.random.Generator(np.random.PCG64(state))


def source_normal(rng):
    u=v=0
    while u==0: u=float(rng.random())
    while v==0: v=float(rng.random())
    return math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v)


def average(values):
    return sum(values)/len(values)


def inner(a,b):
    return sum(x*y for x,y in zip(a,b))


def polynomial(xs,ys,degree):
    """Original polyFit and pivoted Gauss–Jordan, with no fallback needed here."""
    p=degree+1
    a=[[0.0]*p for _ in range(p)];b=[0.0]*p
    for x,y in zip(xs,ys):
        f=[1.0]
        for _ in range(degree): f.append(f[-1]*x)
        for j in range(p):
            b[j]+=f[j]*y
            for k in range(p):a[j][k]+=f[j]*f[k]
    for j in range(p):a[j][j]+=1e-7
    m=[row+[rhs] for row,rhs in zip(a,b)]
    for k in range(p):
        pivot=max(range(k,p),key=lambda i:abs(m[i][k]))
        m[k],m[pivot]=m[pivot],m[k]
        assert abs(m[k][k])>=1e-12, 'Reference fixture must not exercise source pivot substitution'
        divisor=m[k][k]
        for j in range(k,p+1):m[k][j]/=divisor
        for i in range(p):
            if i!=k:
                factor=m[i][k]
                for j in range(k,p+1):m[i][j]-=factor*m[k][j]
    return [row[-1] for row in m]


def predict(coef,x):
    result=0.;power=1.
    for c in coef:result+=c*power;power*=x
    return result


def truth(x):return math.sin(math.pi*x)+.4*x


def polynomial_sample(generator,n,sigma):
    x=[];y=[]
    for _ in range(n):
        xi=-1+2*float(generator.random())
        x.append(xi);y.append(truth(xi)+sigma*source_normal(generator))
    return x,y


@pytest.mark.parametrize('rho,w,seed',[(-.95,0,0),(0,.5,4294967295),(.2,.317,17),(.95,1,2026)])
def test_correlation_all_metrics_and_sampling(rho,w,seed):
    r=client.post('/api/v1/correlation/analyze',json=dict(rho=rho,w=w,seed=seed)).json()
    assert r['theta']==pytest.approx(math.acos(rho),abs=1e-14)
    assert r['theta_degrees']==pytest.approx(math.acos(rho)*180/math.pi,abs=1e-12)
    variance=lambda z:z*z+(1-z)*(1-z)+2*z*(1-z)*rho
    assert r['variance']==pytest.approx(variance(w),abs=1e-14)
    expected_labels={-.95:('Strong negative alignment','Strong cancellation potential'),
                     0:('Near orthogonality','Some diversification benefit'),
                     .2:('Weak positive alignment','Some diversification benefit'),
                     .95:('Strong positive alignment','Little diversification: assets move together')}
    assert (r['interpretation'],r['diversification'])==expected_labels[rho]
    assert np.allclose(r['variance_curve'],[[i/200,variance(i/200)] for i in range(201)],atol=1e-14,rtol=0)
    g=source_rng(seed,'correlation');pairs=[]
    for _ in range(450):
        z1,z2=source_normal(g),source_normal(g)
        pairs.append([z1,rho*z1+math.sqrt(1-rho*rho)*z2])
    assert r['scatter']==pairs
    assert r['seed']==seed


@pytest.mark.parametrize('rho,expected',[(-.500001,'Strong cancellation potential'),(-.5,'Negative correlation helps hedging'),
    (-.000001,'Negative correlation helps hedging'),(0,'Some diversification benefit'),(.399999,'Some diversification benefit'),
    (.4,'Limited diversification'),(.799999,'Limited diversification'),(.8,'Little diversification: assets move together')])
def test_diversification_boundaries(rho,expected):
    assert engine.diversification(rho)==expected


@pytest.mark.parametrize('seed,n,rho,beta1,beta2,sigma',[(0,20,-.95,-2.5,2.5,.05),(4294967295,400,.95,0,0,2.5),(17,120,.45,1.1,.7,.9)])
def test_multiple_every_metric_against_scalar_source(seed,n,rho,beta1,beta2,sigma):
    response=client.post('/api/v1/multiple-regression/analyze',json=locals())
    assert response.status_code==200,response.text
    r=response.json();g=source_rng(seed,'multiple-regression');x1=[];x2=[];y=[]
    for _ in range(n):
        a,b,e=source_normal(g),source_normal(g),source_normal(g)
        v=rho*a+math.sqrt(1-rho*rho)*b
        x1.append(a);x2.append(v);y.append(beta1*a+beta2*v+sigma*e)
    assert r['x1']==x1 and r['x2']==x2 and r['y']==y
    m1,m2,my=average(x1),average(x2),average(y)
    a=[v-m1 for v in x1];b=[v-m2 for v in x2];c=[v-my for v in y]
    s11,s22,s12=inner(a,a),inner(b,b),inner(a,b)
    s1y,s2y=inner(a,c),inner(b,c);det=s11*s22-s12*s12
    b1=(s22*s1y-s12*s2y)/det;b2=(s11*s2y-s12*s1y)/det
    intercept=my-b1*m1-b2*m2
    fitted=[intercept+b1*u+b2*v for u,v in zip(x1,x2)]
    errors=[yi-fi for yi,fi in zip(y,fitted)]
    fc=[fi-average(fitted) for fi in fitted]
    sst,ssr,sse=inner(c,c),inner(fc,fc),inner(errors,errors)
    theta=math.acos(min(1,math.sqrt(max(0,ssr/sst))))
    expected=dict(sst=sst,ssr=ssr,sse=sse,ssr_plus_sse=ssr+sse,r_squared=ssr/sst,
                  theta=theta,theta_degrees=theta*180/math.pi,cos_squared=math.cos(theta)**2,
                  correlation=s12/math.sqrt(s11*s22),determinant=det)
    for key,value in expected.items():assert r[key]==pytest.approx(value,rel=1e-9,abs=1e-10),key
    assert r['coefficients']==pytest.approx([intercept,b1,b2],abs=1e-10)
    assert r['orthogonality']==pytest.approx([inner(a,errors),inner(b,errors)],abs=1e-10)
    assert r['fitted']==pytest.approx(fitted,abs=1e-10)
    assert r['residual']==pytest.approx(errors,abs=1e-10)
    assert r['condition']==pytest.approx(np.linalg.cond([[s11,s12],[s12,s22]]))


@pytest.mark.parametrize('seed,n,degree,sigma,x0',[(0,35,4,.35,.6),(4294967295,15,12,1.2,-1)])
def test_polynomial_all_metrics_and_monte_carlo_source(seed,n,degree,sigma,x0):
    response=client.post('/api/v1/bias-variance/analyze',json=locals())
    assert response.status_code==200,response.text
    r=response.json();x,y=polynomial_sample(source_rng(seed,'polynomial-sample'),n,sigma)
    assert r['x']==x and r['y']==pytest.approx(y,abs=1e-14)
    coef=polynomial(x,y,degree)
    assert r['coefficients']==pytest.approx(coef,rel=1e-6,abs=1e-7)
    train=average([(yi-predict(coef,xi))**2 for xi,yi in zip(x,y)])
    test=average([(predict(coef,-1+2*i/159)-truth(-1+2*i/159))**2 for i in range(160)])
    g=source_rng(seed,'polynomial-monte-carlo');predictions=[]
    for _ in range(80):
        xs,ys=polynomial_sample(g,n,sigma)
        predictions.append(predict(polynomial(xs,ys,degree),x0))
    mp=average(predictions);bias=(mp-truth(x0))**2;variance=sum((p-mp)**2 for p in predictions)/79
    for key,value in dict(train_mse=train,test_mse=test,bias_squared=bias,variance=variance,noise=sigma*sigma,
                          expected_error=bias+variance+sigma*sigma).items():
        assert r[key]==pytest.approx(value,rel=1e-6,abs=1e-8),key
    assert r['predictions']==pytest.approx(predictions,rel=1e-6,abs=1e-7)
    for key,count in [('test_grid',160),('curve',200)]:
        expected=[[-1+2*i/(count-1),truth(-1+2*i/(count-1)),predict(coef,-1+2*i/(count-1))] for i in range(count)]
        assert np.allclose(r[key],expected,rtol=1e-6,atol=1e-7)


def inverse2(a,b,d):
    det=a*d-b*b
    return [[d/det,-b/det],[-b/det,a/det]]


@pytest.mark.parametrize('seed,n,beta,sigma,tau,x0',[(0,10,-2.5,.15,.15,-3),(4294967295,250,2.5,2.5,5,3),(17,50,1.2,.8,1,1.5)])
def test_bayesian_every_metric_and_predictive_curve(seed,n,beta,sigma,tau,x0):
    response=client.post('/api/v1/bayesian/analyze',json=locals())
    assert response.status_code==200,response.text
    r=response.json();g=source_rng(seed,'bayesian');x=[];y=[]
    for _ in range(n):
        xi=source_normal(g);x.append(xi);y.append(.35+beta*xi+sigma*source_normal(g))
    assert r['x']==x and r['y']==y
    sx,sxx,sy,sxy=sum(x),inner(x,x),sum(y),inner(x,y)
    cov=inverse2(n/sigma**2+1/tau**2,sx/sigma**2,sxx/sigma**2+1/tau**2)
    rhs=[sy/sigma**2,sxy/sigma**2];mu=[inner(row,rhs) for row in cov]
    ols=[inner(row,[sy,sxy]) for row in inverse2(n,sx,sxx)]
    sds=[math.sqrt(cov[i][i]) for i in range(2)]
    pvariance=lambda t:sigma**2+cov[0][0]+2*t*cov[0][1]+t*t*cov[1][1]
    assert np.allclose(r['covariance'],cov,atol=1e-12,rtol=1e-12)
    assert r['mean']==pytest.approx(mu,abs=1e-12)
    assert r['standard_deviations']==pytest.approx(sds,abs=1e-12)
    assert r['beta_interval']==pytest.approx([mu[1]-1.96*sds[1],mu[1]+1.96*sds[1]],abs=1e-12)
    assert r['ols']==pytest.approx(ols,abs=1e-12)
    assert r['predictive_variance']==pytest.approx(pvariance(x0),abs=1e-12)
    assert r['predictive_sd']==pytest.approx(math.sqrt(pvariance(x0)),abs=1e-12)
    expected=[]
    for i in range(120):
        t=-3+6*i/119;m=mu[0]+mu[1]*t;v=pvariance(t)
        expected.append([t,m,m-1.96*math.sqrt(v),m+1.96*math.sqrt(v),v])
    assert np.allclose(r['curve'],expected,atol=1e-12,rtol=1e-12)


@pytest.mark.parametrize('name,field',[('correlation','w'),('multiple-regression','beta1'),('bias-variance','sigma'),('bayesian','tau')])
def test_boolean_is_not_a_numeric_parameter(name,field):
    response=client.post(f'/api/v1/{name}/analyze',json={field:True})
    assert response.status_code==422
    assert response.json()['error']['code']=='invalid_request'


def test_small_nonconstant_response_is_not_zero_variance():
    x1=np.array([1.,2.,3.,4.]);x2=np.array([1.,4.,2.,5.]);y=x1+x2
    baseline=engine.multiple_fit(x1,x2,y)
    result=engine.multiple_fit(x1,x2,y*1e-10)
    assert result['r_squared']==pytest.approx(baseline['r_squared'])
    assert result['coefficients']==pytest.approx(np.asarray(baseline['coefficients'])*1e-10,abs=1e-22)


def test_small_full_rank_predictors_are_not_singular():
    x1=np.array([1.,2.,3.,4.]);x2=np.array([1.,4.,2.,5.]);y=x1+x2
    r=engine.multiple_fit(x1*1e-12,x2*1e-12,y)
    assert r['coefficients'][1:]==pytest.approx([1e12,1e12],rel=1e-12)
    assert r['r_squared']==pytest.approx(1)


def test_condition_estimation_failure_is_a_structured_numerical_error(monkeypatch):
    def fail(_):raise np.linalg.LinAlgError('SVD did not converge')
    monkeypatch.setattr(module.engines.np.linalg,'cond',fail)
    r=client.post('/api/v1/multiple-regression/analyze',json={})
    assert r.status_code==422 and r.json()['error']['code']=='numerical_failure'


@pytest.mark.parametrize('diagonal',[[1.,0.],[1.,-.01]])
def test_invalid_covariance_is_not_silently_flattened(diagonal):
    with pytest.raises(engine.NumericalError):engine.ellipse(np.diag(diagonal),np.zeros(2))


def test_covariance_decomposition_failure_is_structured(monkeypatch):
    def fail(_):raise np.linalg.LinAlgError('Eigenvalues did not converge')
    monkeypatch.setattr(module.engines.np.linalg,'eigh',fail)
    r=client.post('/api/v1/bayesian/analyze',json={})
    assert r.status_code==422 and r.json()['error']['code']=='numerical_failure'


@pytest.mark.parametrize('name',['correlation','multiple-regression','bias-variance','bayesian'])
def test_concurrent_requests_preserve_seed_and_full_precision(name):
    url=f'/api/v1/{name}/analyze';payload={'seed':17}
    expected=client.post(url,json=payload).json()
    def request(i):return client.post(url,json=payload if i%2==0 else {'seed':18}).json()
    with ThreadPoolExecutor(max_workers=4) as executor:results=list(executor.map(request,range(8)))
    assert all(results[i]==expected for i in [0,2,4,6])
    assert results[1]!=expected
    # Values are not rounded to the source's displayed 2–6 decimal places.
    key={'correlation':'theta_degrees','multiple-regression':'r_squared','bias-variance':'test_mse','bayesian':'predictive_sd'}[name]
    assert expected[key]!=round(expected[key],6)
