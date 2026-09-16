from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[2]
BACKUP=Path(__file__).parent
OUT=ROOT/'tests/fixtures'
OUT.mkdir(exist_ok=True)

class Controls(HTMLParser):
    def __init__(self):super().__init__();self.inputs=[];self.plots=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='input':self.inputs.append({k:attrs[k] for k in ('id','type','min','max','step','value')})
        if tag in ('canvas','svg'):self.plots.append(attrs['id'])

records=[]
for filename in ['correlation_geometry_interactive_explorer.html','explorer_6_multiple_regression_projection_subspace.html',
                 'explorer_9_bias_variance_polynomial_complexity.html','explorer_11_bayesian_linear_regression_posterior_geometry.html']:
    path=BACKUP/filename;source=path.read_text(encoding='utf-8');parser=Controls();parser.feed(source)
    labels=re.findall(r'<div class="label">(.*?)</div>',source,re.S)
    guide=re.search(r'<section class="quick-reference">(.*?)</section>',source,re.S)
    records.append(dict(file=filename,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),inputs=parser.inputs,
                        plots=parser.plots,metric_labels=labels,quick_reference=guide[1] if guide else None))
(OUT/'regression-source-contract.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'regression-protected-files.json').write_text((BACKUP/'protected-modules.json').read_text(encoding='utf-8-sig'),encoding='utf-8')
