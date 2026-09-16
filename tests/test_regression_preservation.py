from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'modules/regression_geometry_explorers'


def test_controls_plots_metrics_and_guides_match_authoritative_sources():
    class Controls(HTMLParser):
        def __init__(self):super().__init__();self.inputs=[];self.plots=[];self.labels=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='input':self.inputs.append({k:attrs[k] for k in ('id','type','min','max','step','value')})
            if tag in ('canvas','svg'):self.plots.append(attrs['id'])
            if tag=='label' and 'for' in attrs:self.labels.append(attrs['for'])
    baseline=json.loads((ROOT/'tests/fixtures/regression-source-contract.json').read_text(encoding='utf-8'))
    for record in baseline:
        source=(MODULE/record['file']).read_text(encoding='utf-8')
        parser=Controls();parser.feed(source)
        assert parser.inputs==record['inputs'],record['file']
        assert parser.plots==record['plots'],record['file']
        assert all(item['id'] in parser.labels for item in parser.inputs)
        assert re.findall(r'<div class="label">(.*?)</div>',source,re.S)==record['metric_labels']
        if record['quick_reference']:
            assert re.search(r'<section class="quick-reference">(.*?)</section>',source,re.S)[1]==record['quick_reference']


def test_other_modules_have_identical_paths_and_bytes():
    baseline=json.loads((ROOT/'tests/fixtures/regression-protected-files.json').read_text(encoding='utf-8'))
    expected={item['path']:item['sha256'] for item in baseline}
    actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in (ROOT/'modules').iterdir() if directory.name!='regression_geometry_explorers'
            for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    assert actual==expected
