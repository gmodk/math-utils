# Unified Markov CSV schema

The importer accepts comma, semicolon, tab, or pipe delimiters. Quoted fields, escaped quotes, and multiline values are supported.

## Node rows

Set `record_type` to `node` or `state`.

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Stable state identifier. |
| `label` | no | Display label; defaults to `id`. |
| `category` | no | Visibility and styling group. |
| `initial_probability` | no | Component of the initial distribution. Values are normalized when necessary. |
| `reward` | no | Per-step reward used by discounted reward calculations. |

## Transition rows

Set `record_type` to `transition`.

| Field | Required | Meaning |
| --- | --- | --- |
| `source` | yes | Origin state id. |
| `target` | yes | Destination state id. |
| `probability` | yes | Non-negative transition probability. |
| `time` | for time-varying chains | Integer time-slice label; defaults to `0`. |
| `relation` | no | Semantic transition type used by the visibility filter. |
| `confidence` | no | Edge evidence confidence in `[0,1]`; controls visual opacity. |
| `count` | no | Observed transition count used for Dirichlet posterior smoothing. |
| `enabled` | no | Boolean activation flag; defaults to `true`. |

Node rows may be omitted. In that case, states are inferred from the union of source and target identifiers. Unknown columns are retained as row metadata.

The importer blocks replacement when ids are duplicated, endpoints are unknown, a required mapping is absent, probabilities are invalid, or a state has no outgoing mass. Non-unit row sums produce a warning and are normalized in the analytical preview.
