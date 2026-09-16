"""Extract the shipped ZIP and launch its four modules using a provisioned Python."""
from pathlib import Path
import hashlib
import io
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request,urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    archive=ROOT/'math-utils-v1.2.0-ml-knowledge-graph.zip'
    target=Path(tempfile.mkdtemp(prefix='math-utils-v1.2-extraction-')).resolve()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():assert (target/name).resolve().is_relative_to(target)
        z.extractall(target)
    extracted=target/'math-utils'
    assert not (extracted/'.venv').exists()
    manifest=json.loads((extracted/'module-checksums.json').read_text())
    for item in manifest:assert hashlib.sha256((extracted/item['path']).read_bytes()).hexdigest()==item['sha256']
    base=int(os.environ.get('MATH_UTILS_EXTRACTION_PORT','8900'))
    for port in range(base,base+5):
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    flags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    def read(port,path):
        with urlopen(f'http://127.0.0.1:{port}{path}',timeout=15) as r:return r.read()
    def post(path,data):
        request=Request(f'http://127.0.0.1:{base+4}{path}',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=30) as r:return json.load(r)
    with (target/'launch.log').open('w+',encoding='utf-8') as log:
        process=subprocess.Popen([sys.executable,'-B','-X','utf8','launch.py','--skip-install','--no-browser','--port',str(base)],cwd=extracted,env=env,stdout=log,stderr=log,creationflags=flags)
        try:
            deadline=time.monotonic()+90
            while True:
                if process.poll() is not None:
                    log.seek(0);raise RuntimeError(log.read())
                try:
                    status=json.loads(read(base,'/api/status'))
                    if len(status['modules'])==4 and all(m['ready'] for m in status['modules']):break
                except OSError:pass
                assert time.monotonic()<deadline,'Extracted platform startup timeout'
                time.sleep(.25)
            expected=['memory-atlas','markov','symmetric-groups','ml-knowledge-graph']
            assert [m['id'] for m in status['modules']]==expected
            for offset in range(5):assert read(base+offset,'/')
            assert json.loads(read(base+4,'/api/health'))['ready']
            with zipfile.ZipFile(io.BytesIO(read(base+4,'/api/csv/templates/csv-templates.zip'))) as z:
                files=[dict(name=n,text=z.read(n).decode()) for n in z.namelist()]
            graph=post('/api/csv/import',dict(files=files))
            assert len(graph['nodes'])==len(graph['edges'])==4
            edges=post('/api/graph/weights',dict(edges=graph['edges']))
            tda=post('/api/graph/tda',dict(nodes=graph['nodes'],edges=edges,epsilon=1,fillAreas=True))
            assert (tda['beta0'],tda['beta1'],len(tda['activeFaces']))==(1,0,1)
            assert post('/api/graph/export',graph)==graph
        finally:
            if process.poll() is None:process.send_signal(signal.CTRL_BREAK_EVENT if os.name=='nt' else signal.SIGINT)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:process.kill();process.wait();raise
    assert process.returncode==0
    for port in range(base,base+5):
        with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0,f'Port {port} leaked'
    result=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),extracted_to=str(extracted),interpreter=sys.executable,environment='Existing provisioned Python, no source checkout or environment in extracted tree',status=status,template_round_trip='passed',tda_and_export='passed',shutdown_exit_code=process.returncode,ports_released=True,module_hashes=len(manifest))
    (ROOT/'validation-results/ml-integration/extraction.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
