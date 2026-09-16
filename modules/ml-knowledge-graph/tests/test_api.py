import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from app import app
from backend.csv_import import NODE_FIELDS,EDGE_FIELDS

client=TestClient(app)

def files(nodes='id,label\na,Alpha\nb,Beta\n',edges='source,target,relation,directed\na,b,uses,true\n'):
    return {'files':[{'name':'nodes.csv','text':nodes},{'name':'edges.csv','text':edges}]}

def test_health_assets_and_private_paths():
    assert client.get('/api/health').json()['ready'] is True
    for path in ('/','/js/main.js','/constellation/','/vendor/three/build/three.module.js','/vendor/marked/marked.min.js'):
        assert client.get(path).status_code==200
    for path in ('/.git/config','/reference/csv-importer/src/topology.js','/backend/csv_import.py'):
        assert client.get(path).status_code==404
    assert "connect-src 'self'" in client.get('/').headers['content-security-policy']

def test_health_rejects_missing_asset(monkeypatch):
    import app as service
    original=service.Path.is_file
    monkeypatch.setattr(service.Path,'is_file',lambda p: False if p.name=='main.js' else original(p))
    response=client.get('/api/health')
    assert response.status_code==503 and response.json()['ready'] is False

def test_health_validates_layout_against_bundled_graph(monkeypatch):
    import app as service
    monkeypatch.setattr(service,'read_bundled_layout',lambda: {'not-a-bundled-node':[0,0,0]})
    response=client.get('/api/health')
    assert response.status_code==503
    assert response.json()['error']=='Bundled force layout does not match bundled graph'

def test_self_loop_and_undirected_traversal():
    g=client.post('/api/csv/import',json=files(edges='source,target,relation,directed,weight\na,b,related,false,0\na,a,reflects,true,1')).json()
    assert len(g['edges'])==2
    model=client.post('/api/graph/enrich',json=g).json()
    assert model['nodes'][1]['downstream']==['b','a']
    assert model['edges'][0]['weight']==0
    assert client.post('/api/graph/components',json=g).json()==dict(groups=['a'],beta0=1,beta1=1,edges=2)

@pytest.mark.parametrize('kind,fields',[('nodes',NODE_FIELDS),('edges',EDGE_FIELDS)])
def test_template(kind,fields):
    r=client.get(f'/api/csv/templates/{kind}.csv')
    assert r.status_code==200
    assert r.headers['content-type'].startswith('text/csv')
    assert f'filename="{kind}.csv"' in r.headers['content-disposition']
    assert r.text.splitlines()[0].split(',')==fields
    assert len(r.text.splitlines())==5

def test_zip_template_round_trip():
    r=client.get('/api/csv/templates/csv-templates.zip')
    assert r.headers['content-type']=='application/zip'
    assert 'nodes-and-edges.zip' in r.headers['content-disposition']
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.namelist()==['nodes.csv','edges.csv']
        payload={'files':[dict(name=name,text=z.read(name).decode()) for name in z.namelist()]}
    graph=client.post('/api/csv/import',json=payload).json()
    assert len(graph['nodes'])==4 and len(graph['edges'])==4
    assert graph['nodes'][0]['label']=='Example node 1'
    exported=client.post('/api/graph/export',json=graph)
    assert exported.json()==graph

@pytest.mark.parametrize('nodes,edges,column',[
    ('id,id\na,b','source,target\na,b',''),
    ('id,label\na,A\na,B','source,target\na,b','id'),
    ('id,label\na,A','source,target\na,','target'),
    ('id,label\na,A\nb,B','source,target,directed\na,b,perhaps','directed'),
    ('id,label\na,A\nb,B','source,target,strength\na,b,NaN','strength'),
    ('id,label\na,A\nb,B','source,target,evidence_count\na,b,1.5','evidence_count'),
    ('','source,target\na,b',''),
    ('id,label\na,"unclosed','source,target\na,b',''),
    ('id,label\na,A,extra','source,target\na,b',''),
])
def test_actionable_errors(nodes,edges,column):
    payload=files(nodes,edges);preview=client.post('/api/csv/preview',json=payload).json()
    assert preview['errors'] and preview['graph'] is None
    assert all('row' in e and 'column' in e and e['message'] for e in preview['errors'])
    assert any(e['column']==column for e in preview['errors'])
    assert client.post('/api/csv/import',json=payload).status_code==422

def test_headers_mapping_missing_endpoint_and_constraints():
    p=files();p['files'][1]['mapping']={'source':'missing','target':'target'}
    assert client.post('/api/csv/import',json=p).status_code==422
    p=files(edges='source,target,relation\na,c,uses');p['generate_endpoints']=False
    assert client.post('/api/csv/import',json=p).status_code==422
    p['generate_endpoints']=True;r=client.post('/api/csv/import',json=p).json()
    assert r['warnings'] and r['nodes'][-1]['generated_endpoint']
    p=files();p['allowed_relations']=['supports']
    assert client.post('/api/csv/import',json=p).status_code==422

def test_semantics_provenance_and_quoted_values():
    p=files('id,label,notion_id,source_url,description\na,"Alpha, one",notion-a,https://example.org/a,"first\nsecond"\nb,Beta,,,',
      'source,target,relation,directed,weight,strength,confidence,distance,sign,evidence_count,notion_id,source_url,provenance\na,b,custom relation,true,0.3,0.9,0.7,4,-1,2,notion-e,https://example.org/e,provided\na,b,custom relation,false,0.4,0.8,0.6,5,1,3,,,second source')
    graph=client.post('/api/csv/import',json=p).json();n=graph['nodes'][0];e=graph['edges'][0]
    assert n['label']=='Alpha, one' and n['notion_id']=='notion-a'
    assert n['properties']['description']=='first\nsecond'
    assert len(graph['edges'])==2 and graph['edges'][1]['directed'] is False
    assert [e[f] for f in ('weight','strength','confidence','distance','sign','evidence_count')]==[.3,.9,.7,4,-1,2]
    assert e['relation']=='custom relation' and e['source_url']=='https://example.org/e' and e['provenance']=='provided'
    exported=client.post('/api/graph/export',json=graph).json();assert exported==graph
    model=client.post('/api/graph/enrich',json=graph).json()
    assert model['edges'][0]['confidence']==.7
    projected=client.post('/api/fork/graph',json={'graph':graph}).json()
    assert projected['edges'][0]['notion_id']=='notion-e'
    for field in ('weight','strength','confidence','distance','sign','evidence_count'):
        weighted=client.post('/api/graph/weights',json={'edges':graph['edges'],'field':field,'mode':'distance'}).json()
        assert weighted[0][field]==e[field] and 'filterWeight' in weighted[0]

@pytest.mark.parametrize('text,name,counts',[
    ('id,label,connections\na,Alpha,b\nb,Beta,','adjacency.csv',(2,1)),
    ('source,target\na,b','edges.csv',(2,1)),
    ('id,label\na,Alpha','nodes.csv',(1,0)),
])
def test_single_file_modes(text,name,counts):
    r=client.post('/api/csv/import',json={'files':[dict(name=name,text=text)]})
    assert r.status_code==200
    assert (len(r.json()['nodes']),len(r.json()['edges']))==counts

def test_no_fabricated_measurements_or_provenance():
    g=client.post('/api/csv/import',json=files(edges='source,target\na,b')).json();e=g['edges'][0]
    assert e['relation'] is None and e['strength'] is None and e['weight'] is None
    assert 'provenance' not in e and 'type' not in e
    assert client.post('/api/graph/export',json=g).json()['edges'][0].get('type') is None
    assert client.post('/api/graph/enrich',json=g).json()['edges'][0]['type']=='unspecified'

def test_export_strips_only_derived_runtime_state():
    graph=client.post('/api/csv/import',json=files(
        'id,label,notion_id,source_url\na,Alpha,page-a,https://example.org/a\nb,Beta,page-b,',
        'source,target,relation,directed,strength,confidence,distance,sign,evidence_count,notion_id,source_url,provenance\na,b,uses,true,.9,.8,2,-1,3,edge-a,https://example.org/e,fixture')).json()
    enriched=client.post('/api/graph/enrich',json=graph).json()
    exported=client.post('/api/graph/export',json=enriched).json()
    node=exported['nodes'][0];edge=exported['edges'][0]
    assert not ({'x','y','z','homeX','homeY','homeZ','toIds','fromIds','neighborIds','depth','degree','rank','metrics','upstream','downstream'} & node.keys())
    assert not ({'a','b','type','filterWeight','forceWeight'} & edge.keys())
    assert 'metricRanges' not in exported and 'schema' not in exported
    assert node['notion_id']=='page-a' and node['source_url']=='https://example.org/a'
    assert {k:edge[k] for k in ('relation','directed','strength','confidence','distance','sign','evidence_count','notion_id','source_url','provenance')}=={
        'relation':'uses','directed':True,'strength':.9,'confidence':.8,'distance':2,'sign':-1,
        'evidence_count':3,'notion_id':'edge-a','source_url':'https://example.org/e','provenance':'fixture'}

def test_canonical_schema_drives_mapping_and_provenance_aliases():
    schema=client.get('/api/csv/schema').json()
    p=files('id,label,Notion ID,Source URL,color,size\na,Alpha,page-a,https://example.org/a,red,3\nb,Beta,page-b,,blue,4',
            'source,target,relation,Notion ID,Source URL\na,b,uses,page-e,https://example.org/e')
    result=client.post('/api/csv/preview',json=p).json()
    assert set(schema['nodes']).issubset(result['tables'][0]['mapping'])
    assert set(schema['edges'])==set(result['tables'][1]['mapping'])
    assert schema['node_numeric']==['size'] and schema['edge_numeric']==['weight','strength','confidence','distance','sign','evidence_count']
    assert all(field in schema['help'] for field in schema['nodes']+schema['edges'])
    assert result['graph']['nodes'][0]['notion_id']=='page-a'
    assert result['graph']['nodes'][0]['source_url']=='https://example.org/a'
    assert 'url' not in result['graph']['nodes'][0]
    assert result['graph']['nodes'][0]['size']==3
    assert result['graph']['edges'][0]['source_url']=='https://example.org/e'

def test_relation_schema_and_zero_force_weight_remain_distinct():
    g=client.post('/api/csv/import',json=files(edges='source,target,relation,weight,strength\na,b,supports,1,0')).json()
    schema=client.post('/api/graph/schema',json=g).json()
    assert schema['edgeTypes']==['supports']
    weighted=client.post('/api/graph/weights',json={'edges':g['edges'],'field':'strength','mode':'strength'}).json()
    assert weighted[0]['weight']==1 and weighted[0]['strength']==0 and weighted[0]['forceWeight']==.5
    from backend.graph_analysis import force_step
    def moved(force_weight):
        nodes=[dict(id='a',category='x',x=0.,y=0.,z=0.,vx=0.,vy=0.,vz=0.),dict(id='b',category='x',x=200.,y=0.,z=0.,vx=0.,vy=0.,vz=0.)]
        edge=dict(source='a',target='b',relation='supports',weight=1,forceWeight=force_weight)
        options=dict(relations={'supports':1},extra=0,anchor=0,repulsion=0,collision=0,anchors={})
        return force_step(nodes,[edge],options)[0]['x']
    assert moved(0) < moved(1)

def test_fork_force_layout_uses_packaged_cache():
    from pathlib import Path
    cache=json.loads((Path(__file__).parents[1]/'knowledge_graph.layout.json').read_text(encoding='utf-8'))
    graph=client.post('/api/fork/graph',json={}).json()
    result=client.post('/api/fork/layout',json={'nodes':graph['nodes'],'edges':graph['edges'],'layout':'force'}).json()
    assert result==cache['positions']

def test_bundled_fork_data_and_precomputed_metrics_remain():
    from pathlib import Path
    data=json.loads((Path(__file__).parents[1]/'knowledge_graph.json').read_text(encoding='utf-8'))
    projected=client.post('/api/fork/graph',json={}).json()
    assert len(projected['nodes'])==2081 and len(projected['edges'])==5149
    for raw,node in zip(data,projected['nodes']):
        for key,value in raw.items():
            if key not in ('from','to','category','definition','long_description'):assert node[key]==value

def test_filtered_tda_and_directed_traversal():
    g=client.post('/api/csv/import',json=files()).json();model=client.post('/api/graph/enrich',json=g).json()
    assert model['nodes'][0]['downstream']==['a','b']
    assert model['nodes'][1]['downstream']==['b']
    e=client.post('/api/graph/weights',json={'edges':g['edges']}).json()
    r=client.post('/api/graph/tda',json={'nodes':g['nodes'],'edges':e,'epsilon':1,'fillAreas':True}).json()
    assert r['beta0']==1 and r['beta1']==0
