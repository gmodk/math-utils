"""Create and byte-verify the v1.2 release; environments/test output are excluded."""
from pathlib import Path
import hashlib
import json
import zipfile
from release_files import ROOT,files,EXCLUDED

def main():
    paths=files();archive=ROOT/'math-utils-v1.2.0-ml-knowledge-graph.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in paths:
            entry=zipfile.ZipInfo('math-utils/'+p.relative_to(ROOT).as_posix(),(2026,9,15,0,0,0));entry.create_system=3
            entry.external_attr=(0o100755 if p.suffix=='.sh' else 0o100644)<<16;entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for p in paths:assert z.read('math-utils/'+p.relative_to(ROOT).as_posix())==p.read_bytes()
        for name in z.namelist():
            assert not EXCLUDED.intersection(Path(name).parts)
            assert 'regression_geometry_explorers' not in name
        baseline=json.loads((ROOT/'module-checksums.json').read_text(encoding='utf-8'))
        for item in baseline:assert hashlib.sha256(z.read('math-utils/'+item['path'])).hexdigest()==item['sha256']
        listing=z.namelist()
    result=dict(file=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=len(paths),module_files_verified=len(baseline),crc_and_byte_comparison='passed')
    out=ROOT/'validation-results/ml-integration';out.mkdir(exist_ok=True,parents=True)
    (out/'archive-contents.txt').write_text('\n'.join(listing)+'\n',encoding='utf-8')
    (ROOT/(archive.name+'.sha256')).write_text(result['sha256']+'  '+archive.name+'\n')
    (ROOT/'release-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
