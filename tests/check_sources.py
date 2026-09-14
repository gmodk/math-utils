"""Check retained sources without generating files inside vendored modules."""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.active = 'src' not in attrs and attrs.get('type', '') in ('', 'module', 'text/javascript', 'application/javascript')
            self.parts = []
    def handle_data(self, data):
        if self.active:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            if ''.join(self.parts).strip():
                self.scripts.append(''.join(self.parts))
            self.active = False


def main():
    baseline = json.loads((ROOT / 'module-checksums.json').read_text(encoding='utf-8-sig'))
    actual = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'modules').rglob('*') if p.is_file()}
    assert actual == {item['path']: item['sha256'] for item in baseline}, 'Module inventory or bytes changed'
    files = [p for folder in ('modules', 'landing', 'tests') for p in (ROOT / folder).rglob('*') if p.is_file()]
    files.append(ROOT / 'launch.py')
    counts = dict(module_files=len(actual), python=0, javascript_files=0, inline_scripts=0)
    for path in files:
        if path.suffix == '.py':
            compile(path.read_bytes(), str(path), 'exec')
            counts['python'] += 1
        sources = []
        if path.suffix in ('.js', '.mjs'):
            sources = [path.read_text(encoding='utf-8')]
            counts['javascript_files'] += 1
        if path.suffix == '.html':
            parser = Scripts()
            parser.feed(path.read_text(encoding='utf-8'))
            sources = parser.scripts
            counts['inline_scripts'] += len(sources)
        for source in sources:
            result = subprocess.run(['node', '--input-type=module', '--check'], input=source, text=True, encoding='utf-8', capture_output=True)
            assert result.returncode == 0, f'{path}: {result.stderr}'
    print(json.dumps(counts, indent=2))
    (ROOT / 'validation-results/static.json').write_text(json.dumps(counts, indent=2) + '\n')

if __name__ == '__main__':
    main()
