"""One local origin for four statistical explorers. HOST/PORT match S_n's convention."""
from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import engines
from contracts import (CATALOG, Health, Explorer, CorrelationRequest, CorrelationResponse,
                       MultipleRequest, MultipleResponse, BiasRequest, BiasResponse,
                       BayesianRequest, BayesianResponse)

ROOT = Path(__file__).resolve().parent
app = FastAPI(title='Correlation & Regression Explorers',version=engines.VERSION,
              docs_url=None,redoc_url=None)


@app.middleware('http')
async def local_assets_only(request,call_next):
    response=await call_next(request)
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(_request,exc):
    # Never echo non-finite input into JSON serialization.
    fields=[dict(path='.'.join(map(str,e['loc'])),message=e['msg']) for e in exc.errors()]
    return JSONResponse(status_code=422,content={'error':{'code':'invalid_request',
        'message':'Check the highlighted input bounds and types.','fields':fields,'retryable':False}})


@app.exception_handler(engines.NumericalError)
async def numerical_error(_request,exc):
    return JSONResponse(status_code=422,content={'error':{'code':'numerical_failure',
        'message':str(exc),'fields':[],'retryable':False}})


@app.get('/api/health',response_model=Health)
def health():
    return Health(engine_version=engines.VERSION)


@app.get('/api/catalog',response_model=list[Explorer])
def catalog():
    return CATALOG


@app.post('/api/v1/correlation/analyze',response_model=CorrelationResponse)
def correlation(request: CorrelationRequest):
    return engines.correlation(**request.model_dump())


@app.post('/api/v1/multiple-regression/analyze',response_model=MultipleResponse)
def multiple(request: MultipleRequest):
    return engines.multiple_regression(**request.model_dump())


@app.post('/api/v1/bias-variance/analyze',response_model=BiasResponse)
def bias(request: BiasRequest):
    return engines.bias_variance(**request.model_dump())


@app.post('/api/v1/bayesian/analyze',response_model=BayesianResponse)
def bayesian(request: BayesianRequest):
    return engines.bayesian(**request.model_dump())


@app.get('/')
def index():
    return FileResponse(ROOT/'index.html')


def page_endpoint(filename):
    def page(): return FileResponse(ROOT/filename)
    return page


for explorer in CATALOG:
    app.add_api_route(explorer.path,page_endpoint(explorer.path[1:]),methods=['GET'],include_in_schema=False)
for filename in ('README.md','MATHEMATICAL_THEORY.md','MATHEMATICAL_THEORY.docx'):
    app.add_api_route('/'+filename,page_endpoint(filename),methods=['GET'],include_in_schema=False)
app.mount('/static',StaticFiles(directory=ROOT/'static',check_dir=False),name='static')

if __name__=='__main__':
    uvicorn.run(app,host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','8004')))
