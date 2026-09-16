import copy
import json
from pathlib import Path
import subprocess
import pytest
from backend import topology as T,graph_analysis as G

HERE=Path(__file__).parent
FIXTURES=[
 ('triangle',['a','b','c'],[('a','b',.2),('b','c',.3),('c','a',.4)],1,False),
 ('square',['a','b','c','d'],[('a','b',.2),('b','c',.3),('c','d',.4),('d','a',.5)],1,True),
 ('square_before',['a','b','c','d'],[('a','b',.2),('b','c',.3),('c','d',.4),('d','a',.5)],.35,True),
 ('ties',['a','b','c','d','z'],[('a','b',.5),('b','c',.5),('c','d',.5),('d','a',.5),('a','c',.5)],.5,True),
 ('parallel',['a','b','c'],[('a','b',0),('a','b',.8),('b','c',1)],.8,False),
 ('isolated',['a','b'],[],0,False),
 ('empty',[],[],1,True),
 ('face_limit',[f'n{i:02}' for i in range(14)],[(f'n{i:02}',f'n{j:02}',.5) for i in range(14) for j in range(i+1,14)],1,True),
]

def normalize(value):
    if isinstance(value,list):return [normalize(v) for v in value]
    if isinstance(value,dict):
        if 'vertices' in value and 'birth' in value:return {**value,'edges':[e['id'] for e in value['edges']]}
        return {k:normalize(v) for k,v in value.items() if k not in ('nodes','edges') or not isinstance(v,list)}
    return value

def close(a,b,path='root'):
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a:close(a[k],b[k],path+'.'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):close(x,y,f'{path}[{i}]')
    elif isinstance(a,float) or isinstance(b,float):assert a==pytest.approx(b,rel=1e-11,abs=1e-12),path
    else:assert a==b,path

@pytest.mark.parametrize('name,ids,pairs,epsilon,fill',FIXTURES)
def test_original_importer_all_deterministic_methods(name,ids,pairs,epsilon,fill):
    raw=dict(nodes=[dict(id=id,label=id,category='node',properties={}) for id in ids],edges=[dict(id=f'e{i}',source=a,target=b,type='link',weight=w,directed=True) for i,(a,b,w) in enumerate(pairs)])
    oracle=json.loads(subprocess.check_output(['node',str(HERE/'reference_outputs.cjs')],input=json.dumps(dict(graph=raw,epsilon=epsilon,fill=fill)),text=True,encoding='utf-8'))
    golden=HERE/'fixtures'/f'{name}.json'
    assert golden.exists(), 'Golden fixtures must be committed, not generated during tests.'
    close(oracle,json.loads(golden.read_text()))
    g=G.enrich(copy.deepcopy(raw));edges=sorted(g['edges'],key=lambda e:(e['weight'],e['id']))
    for e in edges:e['filterWeight']=e['weight']
    faces=T.detect_faces(g['nodes'],edges);ind=T.independent_faces(edges,faces)
    actual=dict(filtration=T.run_filtration(g['nodes'],edges,epsilon),faces=faces,independent=ind,persistence=T.persistent_homology(g['nodes'],edges,ind),analysis=T.analyze(g['nodes'],edges,epsilon,fill),metrics=[{k:n[k] for k in ('id','depth','degree','rank','metrics','descendantCount','ancestorCount')} for n in g['nodes']],layouts={name:G.targets(g,name,center_id=ids[0] if ids else None) for name in ('semantic','hierarchical','cluster','radial')})
    actual['components']=G.components(g['nodes'],g['edges'])
    actual['weights']={mode:[{k:e[k] for k in ('filterWeight','forceWeight')} for e in T.weights(copy.deepcopy(raw['edges']),mode=mode)] for mode in ('strength','distance')}
    physics=G.enrich(copy.deepcopy(raw))
    options=dict(relations={'link':.6},anchors={'node':G.sphere(0,1,250)},extra=.46,anchor=.38,repulsion=.54,collision=.72)
    actual['physics']=[{k:n[k] for k in ('id','x','y','z','vx','vy','vz')} for n in G.force_step(physics['nodes'],physics['edges'],options,4)]
    # Empty radial center is not a real node; original returns a Map(undefined -> origin).
    if not ids:actual['layouts']['radial']={'undefined':{'x':0,'y':0,'z':0}}
    close(normalize(actual),oracle)
