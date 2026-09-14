from __future__ import annotations
import json, mimetypes, os, sys, traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))

from distributed_memory_atlas.core import Experiment, generate_random_token, available_token_types
from distributed_memory_atlas.approaches import get as get_approach, catalog
from distributed_memory_atlas.approaches import exploration, crypto_lab

STATE={"experiment":Experiment(name="Atlas starter experiment")}
STATE["experiment"].validate()

class Handler(BaseHTTPRequestHandler):
    server_version='DistributedMemoryAtlas/2.1'
    def log_message(self,fmt,*args):
        if os.environ.get('ATLAS_QUIET')!='1': super().log_message(fmt,*args)
    def _json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False,indent=2,default=str).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def _body(self):
        n=int(self.headers.get('Content-Length','0') or 0)
        if not n:return {}
        return json.loads(self.rfile.read(n).decode('utf-8'))
    def _serve(self,path:Path):
        if not path.exists() or not path.is_file():return self._json({'error':'not found'},404)
        data=path.read_bytes();ctype=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        u=urlparse(self.path);path=u.path
        if path=='/api/catalog':return self._json({'approaches':catalog(),'token_types':available_token_types(),'version':'2.1.0'})
        if path=='/api/experiment':return self._json(STATE['experiment'].payload())
        if path.startswith('/api/analyze/'):
            name=path.split('/')[-1]
            try:return self._json(get_approach(name).analyze(STATE['experiment']))
            except Exception as e:return self._json({'error':str(e),'trace':traceback.format_exc() if os.environ.get('ATLAS_DEBUG') else None},400)
        if path.startswith('/api/explore/'):
            try:
                parts=[x for x in path.split('/') if x]
                # /api/explore/<approach>/geometry|graph|region/<id>
                if len(parts)>=4:
                    approach=parts[2]; action=parts[3]; q=parse_qs(u.query)
                    survival=float(q.get('q',['0.9'])[0]); active=q.get('active',['1'])[0].lower() not in {'0','false','no'}
                    if action=='geometry':
                        offset=int(q.get('offset',['0'])[0]);limit=int(q.get('limit',['80'])[0])
                        return self._json(exploration.geometry_payload(STATE['experiment'],approach,q=survival,offset=offset,limit=limit))
                    if action=='graph':
                        limit=int(q.get('limit',['1600'])[0])
                        return self._json({'graph':exploration.graph_payload(STATE['experiment'],approach,active_only=active,q=survival,limit=limit)})
                    if action=='region' and len(parts)>=5:
                        return self._json({'region':exploration.region_detail(STATE['experiment'],approach,int(parts[4]),q=survival)})
            except Exception as e:
                return self._json({'error':str(e),'trace':traceback.format_exc() if os.environ.get('ATLAS_DEBUG') else None},400)
        if path=='/':return self._serve(ROOT/'static'/'index.html')
        if path.startswith('/static/'):
            target=(ROOT/path.lstrip('/')).resolve()
            if ROOT.resolve() not in target.parents:return self._json({'error':'invalid path'},403)
            return self._serve(target)
        if path.startswith('/docs/'):
            target=(ROOT/path.lstrip('/')).resolve()
            if ROOT.resolve() not in target.parents:return self._json({'error':'invalid path'},403)
            return self._serve(target)
        return self._json({'error':'not found'},404)
    def do_POST(self):
        path=urlparse(self.path).path
        try:body=self._body()
        except Exception as e:return self._json({'error':f'invalid JSON: {e}'},400)
        try:
            if path=='/api/random-token':
                result=generate_random_token(int(body.get('dimension',STATE['experiment'].n)),body.get('token_type','natural_numbers'),seed=int(body.get('seed',1)),p=int(body.get('p',STATE['experiment'].p)),object_dimension=body.get('object_dimension'))
                if body.get('apply',True):
                    e=STATE['experiment']; e.p=int(body.get('p',e.p));e.token=result['token'];e.field_projection=result['field_projection'];e.token_type=result['type'];e.seed=result['seed'];e.projection_method=result['projection_method'];e.metadata['generator']=result['parameters']
                    if e.token_type=='cyclic_permutations':e.aggregation='compose'
                    elif e.aggregation=='compose':e.aggregation='mixed'
                    e.validate()
                return self._json({'generated':result,'experiment':STATE['experiment'].payload()})
            if path=='/api/experiment':
                merged=STATE['experiment'].payload()
                merged.update(body)
                STATE['experiment']=Experiment.from_payload(merged)
                return self._json(STATE['experiment'].payload())
            if path=='/api/experiment/import':
                # Import is a new experiment, not a partial update: do not inherit
                # token-dependent fields such as the previous field projection.
                STATE['experiment']=Experiment.from_payload(body)
                return self._json(STATE['experiment'].payload())
            if path=='/api/experiment/reset':
                STATE['experiment']=Experiment(name='Atlas starter experiment');return self._json(STATE['experiment'].payload())
            if path.startswith('/api/explore/') and path.endswith('/crypto'):
                parts=[x for x in path.split('/') if x]
                if len(parts)>=4:
                    approach=parts[2]
                    return self._json(crypto_lab.analyze(
                        STATE['experiment'], approach,
                        policy_type=str(body.get('policy_type','threshold')),
                        threshold=body.get('threshold'),
                        coalition=body.get('coalition'),
                        coalition_fraction=float(body.get('coalition_fraction',0.5)),
                        survival_q=float(body.get('survival_q',body.get('q',0.9))),
                        compromise_q=float(body.get('compromise_q',0.1)),
                        trials=int(body.get('trials',2000)),
                        tamper=bool(body.get('tamper',False)),
                        custom_minimal_sets=body.get('custom_minimal_sets'),
                    ))
            if path.startswith('/api/analyze/'):
                name=path.split('/')[-1];module=get_approach(name)
                kwargs={k:v for k,v in body.items() if k not in {'experiment'}}
                return self._json(module.analyze(STATE['experiment'],**kwargs))
            return self._json({'error':'not found'},404)
        except Exception as e:
            return self._json({'error':str(e),'trace':traceback.format_exc() if os.environ.get('ATLAS_DEBUG') else None},400)

def main():
    host=os.environ.get('ATLAS_HOST','127.0.0.1');port=int(os.environ.get('ATLAS_PORT','8000'))
    print(f'Distributed Memory Architecture Atlas: http://{host}:{port}')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=='__main__':main()
