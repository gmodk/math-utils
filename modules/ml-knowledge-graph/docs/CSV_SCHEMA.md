# CSV schema

Templates and the schema endpoint are generated from `backend/csv_import.py` constants.

Nodes require a mapped ID; label, category, description, url, notion_id, source_url, provenance, color and size are optional. Size must be numeric when supplied. Any other columns are retained as original properties. IDs are strings. Separate edge tables require source and target. An adjacency table uses an ID and connections column with semicolon/comma/pipe-separated endpoint IDs.

Edges support independent relation, directed, weight (legacy scalar), strength, confidence, distance, sign and evidence_count. Numeric blanks are null. Finite numbers are required; evidence_count is a nonnegative integer. Directed accepts true/false, yes/no, y/n, 1/0, directed/undirected; a blank retains the original undirected default. Sign accepts numeric values or positive/negative/+/-.

Relations are unrestricted by default. API callers can pass allowed_relations to constrain them. A preview reports generated endpoint nodes; API callers can set generate_endpoints=false to require complete node tables. Duplicate headers, conflicting node IDs and malformed rows are blocking errors. Original columns are retained separately from normalized values and source-file/row references.

For local provenance, use supplied notion_id, source_url and provenance columns. They are never populated with invented evidence. Export uses JSON to preserve arbitrary properties and all separate edge measurements without narrowing them to a single fixed CSV layout.
