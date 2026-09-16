"""Canonical CSV schema, templates, reviewed mappings, and lossless normalization."""
import csv
import io
import math
import re

NODE_FIELDS = ['id', 'label', 'category', 'description', 'url', 'notion_id', 'source_url', 'provenance', 'color', 'size']
EDGE_FIELDS = ['source', 'target', 'relation', 'directed', 'weight', 'strength', 'confidence', 'distance', 'sign', 'evidence_count', 'notion_id', 'source_url', 'provenance']
NUMERIC = ['weight', 'strength', 'confidence', 'distance', 'sign', 'evidence_count']
ALIASES = {
    'id': ['id', 'node id', 'key', 'uid', 'identifier'],
    'label': ['label', 'name', 'title', 'node', 'concept'],
    'category': ['category', 'group', 'class', 'cluster', 'kind', 'node type', 'type'],
    'source': ['source', 'from', 'src', 'origin', 'parent', 'start'],
    'target': ['target', 'to', 'dst', 'destination', 'child', 'end'],
    'relation': ['relation', 'relationship', 'relation type', 'edge type', 'predicate'],
    'weight': ['weight', 'score', 'cost', 'value'],
    'directed': ['directed', 'directional', 'one way'],
    'color': ['color', 'colour', 'hex'], 'size': ['size', 'radius', 'magnitude', 'importance'],
    # A content URL and an evidence/source URL are distinct provenance fields.
    'url': ['url', 'link', 'href', 'website'],
    'description': ['description', 'detail', 'details', 'summary', 'notes'],
    'adjacency': ['connections', 'connection', 'neighbors', 'neighbours', 'links', 'adjacent', 'targets', 'relations'],
}
for field in EDGE_FIELDS + NODE_FIELDS:
    ALIASES.setdefault(field, [field])

class ImportFailure(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(e['message'] for e in errors))

def issue(file, row, column, message):
    return dict(file=file, row=row, column=column, message=message)

def norm(value):
    return re.sub(r'[\s_-]+', ' ', str(value).strip().lower())

def schema_document():
    """One canonical schema document for API help, preview, and templates."""
    return dict(
        nodes=NODE_FIELDS,
        edges=EDGE_FIELDS,
        numeric=['size'] + NUMERIC,
        node_numeric=['size'],
        edge_numeric=NUMERIC,
        node_required=['id'],
        edge_required=['source','target'],
        help=(
            'Node columns: ' + ', '.join(NODE_FIELDS) + '. ID is required. '
            'Edge columns: ' + ', '.join(EDGE_FIELDS) + '. Source and target are required. '
            'Node size and all edge measurement columns must be numeric when supplied. '
            'Keep relation, directed, legacy weight, strength, confidence, distance, sign, '
            'evidence_count, Notion IDs, source URLs, and provenance separate; leave unavailable values blank.'
        ),
    )

def best(headers, field, excluded=()):
    choices = ALIASES.get(field, [field])
    strict = field in set(EDGE_FIELDS) | {'url','notion_id','source_url','provenance'}
    scored = []
    for h in headers:
        if h in excluded:
            continue
        n = norm(h)
        score = max((100-i if n == norm(t) else 60-i if not strict and n and (n in norm(t) or norm(t) in n) else 0
                     for i, t in enumerate(choices)), default=0)
        if score:
            scored.append((score, -headers.index(h), h))
    return max(scored)[2] if scored else ''

def parse_table(name, text, role=None, mapping=None):
    text = text.lstrip('\ufeff')
    if not text.strip():
        raise ImportFailure([issue(name, 1, '', 'File is empty; include a header and data rows.')])
    # Match the source delimiter scoring, including its stable candidate ordering.
    lines = [x for x in text.splitlines() if x][:8]
    scores = []
    for delimiter in [',', ';', '\t', '|']:
        counts = []
        for line in lines:
            quoted = False; count = 0; i = 0
            while i < len(line):
                if line[i] == '"':
                    if quoted and i+1 < len(line) and line[i+1] == '"': i += 1
                    else: quoted = not quoted
                elif not quoted and line[i] == delimiter: count += 1
                i += 1
            if count: counts.append(count)
        avg = sum(counts)/len(counts) if counts else 0
        score = len(counts)*10 + avg - 2*sum(abs(x-avg) for x in counts)/len(counts) if counts else -1
        scores.append(score)
    delimiter = [',', ';', '\t', '|'][scores.index(max(scores))]
    reader = csv.reader(io.StringIO(text, newline=''), delimiter=delimiter, strict=True)
    try:
        headers = [x.strip() for x in next(reader)]
        if not all(headers) or len(set(headers)) != len(headers):
            raise ImportFailure([issue(name, 1, '', 'Headers must be non-empty and unique.')])
        rows = []; row_numbers = []
        for values in reader:
            if not any(x.strip() for x in values): continue
            if len(values) != len(headers):
                raise ImportFailure([issue(name, reader.line_num, '', f'Expected {len(headers)} cells; found {len(values)}. Quote commas inside values.')])
            rows.append(dict(zip(headers, (x.strip() for x in values))))
            row_numbers.append(reader.line_num)
    except csv.Error as exc:
        raise ImportFailure([issue(name, reader.line_num, '', f'Malformed CSV: {exc}. Check quotation marks.')]) from exc
    if not rows:
        raise ImportFailure([issue(name, 2, '', 'No data rows were found.')])
    source = best(headers, 'source'); target = best(headers, 'target', [source])
    adjacency = best(headers, 'adjacency')
    if role is None:
        role = 'edges' if source and target else 'adjacency' if adjacency else 'nodes'
        if re.search('node|vertex|entit', norm(name)) and role != 'adjacency': role = 'nodes'
    if role not in ('nodes', 'edges', 'adjacency', 'ignore'):
        raise ImportFailure([issue(name, 1, '', 'Choose nodes, edges, adjacency, or ignore.')])
    if mapping is None:
        fields = EDGE_FIELDS if role == 'edges' else NODE_FIELDS + ['adjacency']
        mapping = {f: best(headers, f) for f in fields}
        if role != 'edges':
            mapping['id'] = best(headers, 'id') or headers[0]
            mapping['label'] = best(headers, 'label', [mapping['id']]) or mapping['id']
    return dict(name=name, role=role, mapping=mapping, headers=headers, rows=rows, row_numbers=row_numbers, delimiter=delimiter)

def normalize(tables, allowed_relations=None, generate_endpoints=True):
    nodes = {}; edges = []; errors = []; warnings = []
    def err(t, i, column, message):
        errors.append(issue(t['name'], t['row_numbers'][i], column, message))
    def number(t, i, row, column, field):
        value = row.get(column, '') if column else ''
        if value == '': return None
        if field == 'sign' and value.lower() in ('positive', 'negative', '+', '-'):
            return 1 if value.lower() in ('positive', '+') else -1
        try:
            n = float(value)
            if not math.isfinite(n): raise ValueError()
            if field == 'evidence_count' and (n < 0 or not n.is_integer()): raise ValueError()
            return int(n) if field in ('sign', 'evidence_count') and n.is_integer() else n
        except ValueError:
            err(t, i, column, f'{field} must be a finite number' + (' and a nonnegative integer.' if field == 'evidence_count' else '.'))
            return None
    for t in tables:
        if t['role'] == 'ignore': continue
        required = ['source', 'target'] if t['role'] == 'edges' else ['id'] + (['adjacency'] if t['role'] == 'adjacency' else [])
        for field in required:
            if t['mapping'].get(field) not in t['headers']:
                errors.append(issue(t['name'], 1, field, f'Map {field} to an existing column.'))
        for field, column in t['mapping'].items():
            if column and column not in t['headers']:
                errors.append(issue(t['name'], 1, column, f'Mapped {field} column does not exist.'))
    if errors: raise ImportFailure(errors)
    for t in tables:
        if t['role'] not in ('nodes', 'adjacency'): continue
        m = t['mapping']
        for i, row in enumerate(t['rows']):
            id = row[m['id']]
            if not id:
                err(t, i, m['id'], 'Node ID cannot be empty.'); continue
            node = {'id': id, 'label': row.get(m.get('label')) or id, 'category': row.get(m.get('category')) or 'node', 'properties': dict(row), '_csv_rows': [dict(file=t['name'], row=t['row_numbers'][i])]}
            for field in ('color', 'url', 'description'):
                if row.get(m.get(field)): node[field] = row[m[field]]
            if m.get('size'):
                node['size'] = number(t, i, row, m['size'], 'size')
            for field in ('notion_id', 'source_url', 'provenance'):
                if m.get(field) in row: node[field] = row[m[field]]
            if id in nodes:
                if nodes[id]['properties'] != row:
                    err(t, i, m['id'], f'Duplicate node ID {id!r} has conflicting data; use a unique ID.')
                else:
                    nodes[id]['_csv_rows'].extend(node['_csv_rows'])
                    warnings.append(issue(t['name'], t['row_numbers'][i], m['id'], f'Identical duplicate node {id!r} merged; row references retained.'))
            else: nodes[id] = node
    for t in tables:
        if t['role'] not in ('edges', 'adjacency'): continue
        m = t['mapping']
        for i, row in enumerate(t['rows']):
            if t['role'] == 'adjacency':
                pairs = [(row[m['id']], v.strip()) for v in re.split('[;,|]', row[m['adjacency']]) if v.strip()]
            else: pairs = [(row[m['source']], row[m['target']])]
            for source, target in pairs:
                if not source or not target:
                    err(t, i, m.get('source') if not source else m.get('target'), 'Edge endpoint cannot be empty.'); continue
                relation = row.get(m.get('relation')) or None
                if allowed_relations is not None and relation not in allowed_relations:
                    err(t, i, m.get('relation', 'relation'), f'Unknown relation {relation!r}; allowed: {", ".join(allowed_relations)}.')
                raw_directed = row.get(m.get('directed'), '').lower()
                if raw_directed not in ('', '1', 'true', 'yes', 'y', 'directed', '0', 'false', 'no', 'n', 'undirected'):
                    err(t, i, m.get('directed'), 'Use true/false, yes/no, or 1/0 for directed.')
                edge = dict(id=f'e{len(edges)+1}', source=source, target=target, relation=relation, directed=raw_directed in ('1','true','yes','y','directed'), properties=dict(row), _csv_rows=[dict(file=t['name'], row=t['row_numbers'][i])])
                for field in NUMERIC: edge[field] = number(t, i, row, m.get(field), field)
                for field in ('notion_id', 'source_url', 'provenance'):
                    if m.get(field) in row: edge[field] = row[m[field]]
                for endpoint in (source, target):
                    if endpoint not in nodes:
                        if not generate_endpoints:
                            err(t, i, 'source/target', f'Unknown endpoint {endpoint!r}; supply its node row.')
                        else:
                            nodes[endpoint] = dict(id=endpoint, label=endpoint, category='node', properties={}, generated_endpoint=True)
                            warnings.append(issue(t['name'], t['row_numbers'][i], 'source/target', f'Generated node for endpoint {endpoint!r}.'))
                edges.append(edge)
    if errors: raise ImportFailure(errors)
    if not nodes: raise ImportFailure([issue('', 1, '', 'No nodes created. Check mappings and ignored files.')])
    return dict(format='ml-knowledge-graph/csv-v1', nodes=list(nodes.values()), edges=edges, warnings=warnings)

def preview(payload):
    tables = []; errors = []
    for item in payload.get('files', []):
        try: tables.append(parse_table(item['name'], item.get('text', ''), item.get('role'), item.get('mapping')))
        except ImportFailure as exc: errors.extend(exc.errors)
    graph = None
    if not errors:
        try: graph = normalize(tables, payload.get('allowed_relations'), payload.get('generate_endpoints', True))
        except ImportFailure as exc: errors.extend(exc.errors)
    return dict(schema=schema_document(),tables=tables, errors=errors, warnings=graph['warnings'] if graph else [], graph=graph)

def template(kind):
    fields = NODE_FIELDS if kind == 'nodes' else EDGE_FIELDS if kind == 'edges' else ['id','label','category','connections']
    if kind == 'nodes':
        rows = [dict(id=f'n{i}', label=f'Example node {i}', category='example') for i in range(1,5)]
    elif kind == 'edges':
        rows = [dict(source=f'n{i}', target=f'n{1 if i==4 else i+1}', relation='example_link', directed='true', weight=str(i/5), strength=str(1-i/10), confidence='0.8', distance=str(i), sign='1', evidence_count='1') for i in range(1,5)]
    elif kind == 'adjacency': rows = [dict(id='a', label='Alpha', category='example', connections='b'), dict(id='b', label='Beta', category='example', connections='')]
    else: raise KeyError(kind)
    out = io.StringIO(newline=''); writer = csv.DictWriter(out, fields, lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    return out.getvalue()
