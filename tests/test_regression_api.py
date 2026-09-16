from pathlib import Path
import importlib.util
import sys
import pytest
from fastapi.testclient import TestClient

MODULE=Path(__file__).resolve().parents[1]/'modules/regression_geometry_explorers'
sys.path.insert(0,str(MODULE))
spec=importlib.util.spec_from_file_location('regression_app',MODULE/'app.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client=TestClient(module.app)


def test_health_and_catalog():
    assert client.get('/api/health').json()['explorers']==4
    assert len(client.get('/api/catalog').json())==4


@pytest.mark.parametrize('name', ['correlation','multiple-regression','bias-variance','bayesian'])
def test_defaults_and_seed(name):
    url=f'/api/v1/{name}/analyze'
    response=client.post(url,json={})
    assert response.status_code==200,response.text
    assert response.json()['seed']==2026
    assert response.json()==client.post(url,json={}).json()


@pytest.mark.parametrize('name,fields',[
    ('correlation',{'rho':[-.96,.96],'w':[-.01,1.01]}),
    ('multiple-regression',{'beta1':[-2.51,2.51],'beta2':[-2.51,2.51],'rho':[-.96,.96],'sigma':[0,2.51],'n':[19,401,20.5]}),
    ('bias-variance',{'degree':[0,13,1.5],'sigma':[0,1.21],'n':[14,101],'x0':[-1.01,1.01]}),
    ('bayesian',{'beta':[-2.51,2.51],'sigma':[.14,2.51],'tau':[.14,5.01],'n':[9,251],'x0':[-3.01,3.01]})])
def test_bounds(name,fields):
    for key,values in fields.items():
        for value in values:
            response=client.post(f'/api/v1/{name}/analyze',json={key:value})
            assert response.status_code==422,(key,value,response.text)
            assert response.json()['error']['code']=='invalid_request'


@pytest.mark.parametrize('name,field',[('correlation','rho'),('multiple-regression','sigma'),('bias-variance','sigma'),('bayesian','tau')])
def test_nonfinite_and_unknown(name,field):
    for value in ['NaN','Infinity','-Infinity']:
        r=client.post(f'/api/v1/{name}/analyze',content='{"'+field+'":'+value+'}',headers={'Content-Type':'application/json'})
        assert r.status_code==422 and r.json()['error']['code']=='invalid_request'
    for body in [{'seed':-1},{'seed':4294967296},{'seed':True},{'seed':1.2},{'unknown':1}]:
        assert client.post(f'/api/v1/{name}/analyze',json=body).status_code==422


def test_numerical_error_is_structured(monkeypatch):
    def fail(**_): raise module.engines.NumericalError('Singular test design')
    monkeypatch.setattr(module.engines,'multiple_regression',fail)
    r=client.post('/api/v1/multiple-regression/analyze',json={})
    assert r.status_code==422 and r.json()['error']['code']=='numerical_failure'


def test_local_assets_and_no_statistical_javascript():
    import re
    pages=[MODULE/'index.html',*[MODULE/e.path[1:] for e in module.CATALOG]]
    assert len(list(MODULE.glob('*.html')))==5
    for page in pages:
        response=client.get('/' if page.name=='index.html' else '/'+page.name)
        assert response.status_code==200
        source=page.read_text(encoding='utf-8')
        assert '<script>' not in source
        for asset in re.findall(r'(?:src|href)="(/static/[^"]+)"',source):
            assert client.get(asset).status_code==200
    for asset in (MODULE/'static').iterdir():
        assert client.get('/static/'+asset.name).status_code==200
    for path in pages+list((MODULE/'static').glob('*.js')):
        source=path.read_text(encoding='utf-8')
        for forbidden in ['node_modules','npm','cdn.','https://','randn','solveLinear','polyFit','invert2','Math.random','Math.acos','Math.log','varianceTwoAsset']:
            assert forbidden not in source,(path.name,forbidden)
    assert client.get('/engines.py').status_code==404
    assert client.get('/explorer_2_covariance_ellipsoid_pca_3d.html').status_code==404
