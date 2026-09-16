"""Local static frontend plus Python graph/CSV/TDA API."""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import zipfile
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from backend import csv_import, topology, graph_analysis, fork_graph

ROOT=Path(__file__).resolve().parent
app=FastAPI(title='ML Knowledge Graph',version='1.2.0')

DERIVED_NODE_FIELDS={
    'x','y','z','vx','vy','vz','homeX','homeY','homeZ','toIds','fromIds','neighborIds',
    'depth','upstream','downstream','degree','inDegree','outDegree','rank','metrics',
    'descendantCount','ancestorCount','_p','_radius','_dragging','layoutTarget',
}
DERIVED_EDGE_FIELDS={'a','b','type','filterWeight','forceWeight'}

def read_bundled_layout():
    layout=json.loads((ROOT/'knowledge_graph.layout.json').read_text(encoding='utf-8'))
    positions=layout.get('positions')
    if not isinstance(positions,dict) or not positions:
        raise ValueError('Bundled force layout has no positions')
    return positions

def canonical_export(payload):
    """Remove presentation state while retaining imported facts and provenance."""
    result=copy.deepcopy(payload)
    result.pop('metricRanges',None);result.pop('schema',None)
    result['nodes']=[{k:v for k,v in node.items() if k not in DERIVED_NODE_FIELDS} for node in result['nodes']]
    result['edges']=[{k:v for k,v in edge.items() if k not in DERIVED_EDGE_FIELDS} for edge in result['edges']]
    return result

@app.middleware('http')
async def local_assets_only(request,call_next):
    response=await call_next(request)
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; frame-src 'self'"
    response.headers['X-Content-Type-Options']='nosniff'
    return response

@app.exception_handler(csv_import.ImportFailure)
async def invalid_import(request,exc):
    return JSONResponse(status_code=422,content={'errors':exc.errors})

@app.get('/api/health')
def health():
    required=['index.html','knowledge_graph.json','knowledge_graph.layout.json','js/main.js','constellation/index.html','vendor/three/build/three.module.js','vendor/katex/katex.min.js','vendor/marked/marked.min.js']
    missing=[p for p in required if not (ROOT/p).is_file()]
    if missing:return JSONResponse(status_code=503,content={'ready':False,'missing':missing})
    try:
        raw=json.loads((ROOT/'knowledge_graph.json').read_text(encoding='utf-8'))
        if not isinstance(raw,list) or not raw:raise ValueError('Empty bundled graph')
        positions=read_bundled_layout()
        ids={item.get('id') for item in raw}
        if set(positions)!=ids:raise ValueError('Bundled force layout does not match bundled graph')
    except (ValueError,OSError) as exc:return JSONResponse(status_code=503,content={'ready':False,'error':str(exc)})
    return {'ready':True,'module':'ml-knowledge-graph','version':'1.2.0','nodes':len(raw),'layout_positions':len(positions)}

@app.get('/api/csv/schema')
def schema():return csv_import.schema_document()

@app.get('/api/csv/templates/{filename}')
def templates(filename:str):
    if filename=='csv-templates.zip':
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            for kind in ('nodes','edges'):z.writestr(kind+'.csv',csv_import.template(kind))
        return Response(buf.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="ml-knowledge-graph-nodes-and-edges.zip"'})
    kind=filename.removesuffix('.csv')
    if kind not in ('nodes','edges','adjacency'):raise HTTPException(404)
    return Response(csv_import.template(kind),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{kind}.csv"'})

@app.post('/api/csv/preview')
def preview(payload:dict):return csv_import.preview(payload)

@app.post('/api/csv/import')
def import_csv(payload:dict):
    result=preview(payload)
    if result['errors']:return JSONResponse(status_code=422,content=result)
    return result['graph']

@app.post('/api/csv/parse')
def parse(payload:dict):return csv_import.parse_table(payload.get('name','table.csv'),payload.get('text',''),payload.get('role'),payload.get('mapping'))

@app.post('/api/csv/normalize')
def normalize(payload:dict):return csv_import.normalize(payload['tables'])

@app.post('/api/graph/enrich')
def enrich(payload:dict):return graph_analysis.enrich(payload)

@app.post('/api/graph/schema')
def display_schema(payload:dict):return graph_analysis.display_schema(payload['nodes'],payload['edges'])

@app.post('/api/graph/layout')
def layout(payload:dict):return graph_analysis.targets(payload['graph'],payload['layout'],payload.get('key','category'),payload.get('center'))

@app.post('/api/graph/physics')
def physics(payload:dict):return graph_analysis.force_step(payload['nodes'],payload['edges'],payload['options'],payload.get('steps',1))

@app.post('/api/graph/anchors')
def anchors(payload:dict):
    categories=sorted({n.get('category') or 'node' for n in payload['nodes']})
    return {key:graph_analysis.sphere(i,len(categories),max(250,len(categories)*34)) for i,key in enumerate(categories)}

@app.post('/api/graph/stir')
def stir(payload:dict):
    import random
    for n in payload['nodes']:
        for k in ('vx','vy','vz'):n[k]+=(random.random()-.5)*9
    return payload['nodes']

@app.post('/api/graph/weights')
def weights(payload:dict):return topology.weights(payload['edges'],payload.get('field','weight'),payload.get('mode','strength'))

@lru_cache(maxsize=12)
def cached_tda(serialized):
    p=json.loads(serialized);return topology.analyze(p['nodes'],p['edges'],p.get('epsilon',.52),p.get('fillAreas',False))

@app.post('/api/graph/tda')
def tda(payload:dict):
    # Keys and ordering are part of the original filtration's tie-breaking rules.
    return cached_tda(json.dumps(payload,sort_keys=True))

@app.post('/api/graph/traverse')
def traverse(payload:dict):return graph_analysis.traverse(payload['start'],{n['id']:n for n in payload['nodes']},payload['key'],payload.get('limit'))

@app.post('/api/graph/components')
def components(payload:dict):return graph_analysis.components(payload['nodes'],payload['edges'])

@app.post('/api/graph/export')
def export(payload:dict):
    if not isinstance(payload.get('nodes'),list) or not isinstance(payload.get('edges'),list):raise HTTPException(422,'Expected nodes and edges arrays')
    result=canonical_export(payload)
    return Response(json.dumps(result,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="ml-knowledge-graph.json"'})

@app.post('/api/fork/graph')
def fork_data(payload:dict):
    raw=payload.get('graph')
    if raw is None:raw=json.loads((ROOT/'knowledge_graph.json').read_text(encoding='utf-8'))
    return fork_graph.project(raw)

@lru_cache(maxsize=12)
def cached_fork_layout(serialized):
    p=json.loads(serialized);return fork_graph.layout(p['nodes'],p['edges'],p['layout'],p.get('center'))

@app.post('/api/fork/layout')
def fork_layout(payload:dict):
    if payload.get('layout')=='force' and not any('properties' in n for n in payload.get('nodes',[])):
        cached=read_bundled_layout()
        if set(cached)=={n['id'] for n in payload['nodes']}:return cached
    return cached_fork_layout(json.dumps(payload,sort_keys=True))

app.mount('/constellation',StaticFiles(directory=ROOT/'constellation',html=True),name='constellation')
# Expose only frontend directories, never source references, dotfiles or development configuration.
for directory in ('js','assets','vendor'):
    (ROOT/directory).mkdir(exist_ok=True)
    app.mount('/'+directory,StaticFiles(directory=ROOT/directory),name=directory)

@app.get('/')
def index():return Response((ROOT/'index.html').read_text(encoding='utf-8'),media_type='text/html')

@app.get('/{filename}')
def static_file(filename:str):
    if filename not in ('style.css','knowledge_graph.json','knowledge_graph.layout.json'):raise HTTPException(404)
    path=ROOT/filename
    if not path.is_file():raise HTTPException(404)
    return Response(path.read_bytes(),media_type='text/css' if filename.endswith('.css') else 'application/json')

if __name__=='__main__':
    import uvicorn
    parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8004);parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args();uvicorn.run(app,host=args.host,port=args.port)
