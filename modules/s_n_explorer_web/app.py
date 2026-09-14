"""Dependency-free HTTP server for the S_n Explorer web GUI.

Run:
    python app.py
Then open http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import math
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from dihedral_visualization import geometry, animation_metadata

from symmetric_group import (
    all_subgroups_sn,
    build_dihedral_group,
    cayley_table,
    compose,
    conjugacy_class_summaries,
    cycle_notation,
    generate_permutations,
    generate_subgroup,
    inverse,
    is_normal_subgroup,
    is_self_inverse,
    one_line_notation,
    order_and_sign,
    permutation_record,
    permutation_tuples,
    quotient_element_order,
    quotient_group,
)

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
MAX_N = 8
MAX_CAYLEY_N = 4
MAX_SUBGROUP_N = 4
MAX_GENERATED_SUBGROUP_N = 7


def parse_int(params: dict, name: str, default: int, minimum: int, maximum: int) -> int:
    raw = params.get(name, [str(default)])[0]
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must satisfy {minimum} <= {name} <= {maximum}")
    return value


def serialize_dihedral(m: int) -> list[dict]:
    rows = []
    for index, item in enumerate(build_dihedral_group(m)):
        p = item["permutation"]
        o, s = order_and_sign(p)
        rows.append(
            {
                **item,
                "one_line": one_line_notation(p),
                "cycles": cycle_notation(p),
                "order": o,
                "parity": "even" if s == 1 else "odd",
                "animation": animation_metadata(item, m, index % m),
            }
        )
    return rows


def subgroup_payload(n: int) -> tuple[list[list[list[int]]], list[dict]]:
    elements = generate_permutations(n)
    cached = all_subgroups_sn(n)
    subgroups = [[list(p) for p in subgroup] for subgroup in cached]
    summaries = []
    for idx, subgroup in enumerate(subgroups, start=1):
        normal = is_normal_subgroup(subgroup, elements)
        summaries.append(
            {
                "index": idx,
                "order": len(subgroup),
                "normal": normal,
                "kind": (
                    "trivial"
                    if len(subgroup) == 1
                    else "whole group"
                    if len(subgroup) == len(elements)
                    else "proper"
                ),
                "members": [
                    {
                        "one_line": one_line_notation(p),
                        "cycles": cycle_notation(p),
                    }
                    for p in subgroup
                ],
            }
        )
    return subgroups, summaries


class ExplorerHandler(BaseHTTPRequestHandler):
    server_version = "SnExplorer/2.0"

    def log_message(self, fmt: str, *args) -> None:
        # Keep console output compact while still showing requests.
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send_json(self, payload: dict | list, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_file(STATIC / "index.html")
                return
            if parsed.path.startswith("/static/"):
                relative = parsed.path.removeprefix("/static/")
                candidate = (STATIC / relative).resolve()
                if STATIC.resolve() not in candidate.parents:
                    self.send_error(HTTPStatus.FORBIDDEN)
                    return
                self._send_file(candidate)
                return
            if parsed.path.startswith("/api/"):
                self._handle_api_get(parsed.path, parse_qs(parsed.query))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
        except Exception as exc:  # defensive boundary for the local explorer
            self._send_json({"error": f"Internal error: {exc}"}, 500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            payload = self._read_json()
            self._handle_api_post(parsed.path, payload)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self._send_json({"error": f"Internal error: {exc}"}, 500)

    def _handle_api_get(self, path: str, params: dict) -> None:
        if path == "/api/health":
            self._send_json({"status": "ok", "app": "S_n Explorer Web"})
            return

        if path == "/api/group":
            n = parse_int(params, "n", 4, 1, MAX_N)
            page = parse_int(params, "page", 1, 1, 100000)
            page_size = parse_int(params, "page_size", 25, 5, 100)
            query = params.get("query", [""])[0].strip().lower()
            filter_name = params.get("filter", ["all"])[0].strip().lower()
            if filter_name not in {"all", "even", "odd", "involutions", "identity"}:
                raise ValueError("Unknown element filter")

            tuples = permutation_tuples(n)
            selected = []
            even_count = 0
            odd_count = 0
            involution_count = 0

            for i, p in enumerate(tuples, start=1):
                o, s = order_and_sign(p)
                self_inv = is_self_inverse(p)
                even_count += int(s == 1)
                odd_count += int(s == -1)
                involution_count += int(self_inv)

                include = (
                    filter_name == "all"
                    or (filter_name == "even" and s == 1)
                    or (filter_name == "odd" and s == -1)
                    or (filter_name == "involutions" and self_inv)
                    or (filter_name == "identity" and i == 1)
                )
                if not include:
                    continue

                if query:
                    haystack = f"{i} {one_line_notation(p)} {cycle_notation(p)} {o} {'even' if s == 1 else 'odd'}".lower()
                    if query not in haystack:
                        continue
                selected.append((i, p))

            total_filtered = len(selected)
            pages = max(1, math.ceil(total_filtered / page_size))
            page = min(page, pages)
            start = (page - 1) * page_size
            rows = [permutation_record(i, p) for i, p in selected[start : start + page_size]]

            self._send_json(
                {
                    "n": n,
                    "order": math.factorial(n),
                    "counts": {
                        "even": even_count,
                        "odd": odd_count,
                        "self_inverse": involution_count,
                    },
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "pages": pages,
                        "total_filtered": total_filtered,
                    },
                    "elements": rows,
                    "limits": {
                        "max_n": MAX_N,
                        "cayley_max_n": MAX_CAYLEY_N,
                        "subgroups_max_n": MAX_SUBGROUP_N,
                    },
                }
            )
            return

        if path == "/api/permutation":
            n = parse_int(params, "n", 4, 1, MAX_N)
            idx = parse_int(params, "index", 1, 1, math.factorial(n))
            p = permutation_tuples(n)[idx - 1]
            self._send_json(permutation_record(idx, p))
            return

        if path == "/api/cayley":
            n = parse_int(params, "n", 3, 1, MAX_CAYLEY_N)
            elements = generate_permutations(n)
            table = cayley_table(elements)
            self._send_json(
                {
                    "n": n,
                    "order": len(elements),
                    "labels": [cycle_notation(p) for p in elements],
                    "one_line": [one_line_notation(p) for p in elements],
                    "table": [[value + 1 for value in row] for row in table],
                    "convention": "entry(row sigma, column tau) = index of sigma o tau; tau acts first",
                }
            )
            return

        if path == "/api/dihedral":
            m = parse_int(params, "m", 5, 3, 24)
            self._send_json(
                {
                    "m": m,
                    "order": 2 * m,
                    "vertices": list(range(m)),
                    "geometry": geometry(m),
                    "elements": serialize_dihedral(m),
                    "relations": [f"r^{m} = e", "s^2 = e", "s r s = r^{-1}"],
                }
            )
            return

        if path == "/api/subgroups":
            n = parse_int(params, "n", 3, 1, MAX_SUBGROUP_N)
            _, summaries = subgroup_payload(n)
            self._send_json(
                {
                    "n": n,
                    "group_order": math.factorial(n),
                    "count": len(summaries),
                    "subgroups": summaries,
                }
            )
            return

        if path == "/api/quotient":
            n = parse_int(params, "n", 3, 1, MAX_SUBGROUP_N)
            subgroup_index = parse_int(params, "subgroup", 1, 1, 10000)
            subgroups, summaries = subgroup_payload(n)
            if subgroup_index > len(subgroups):
                raise ValueError("subgroup index is out of range")
            subgroup = subgroups[subgroup_index - 1]
            if not summaries[subgroup_index - 1]["normal"]:
                raise ValueError("The selected subgroup is not normal")
            elements = generate_permutations(n)
            q = quotient_group(subgroup, elements)
            q_payload = {
                "order": q["order"],
                "identity_coset": q["identity_idx"] + 1,
                "table": [[value + 1 for value in row] for row in q["table"]],
                "cosets": [
                    {
                        "index": i + 1,
                        "identity": i == q["identity_idx"],
                        "members": [cycle_notation(p) for p in coset],
                        "representative": cycle_notation(coset[0]),
                        "order": quotient_element_order(q["table"], q["identity_idx"], i),
                    }
                    for i, coset in enumerate(q["cosets"])
                ],
            }
            self._send_json(
                {
                    "n": n,
                    "subgroup_index": subgroup_index,
                    "subgroup_order": len(subgroup),
                    "quotient": q_payload,
                }
            )
            return

        if path == "/api/conjugacy":
            n = parse_int(params, "n", 4, 1, MAX_N)
            summaries = conjugacy_class_summaries(n)
            self._send_json(
                {
                    "n": n,
                    "group_order": math.factorial(n),
                    "class_count": len(summaries),
                    "classes": summaries,
                }
            )
            return

        raise ValueError("Unknown API endpoint")

    def _handle_api_post(self, path: str, payload: dict) -> None:
        if path == "/api/compose":
            n = int(payload.get("n", 4))
            if not 1 <= n <= MAX_N:
                raise ValueError(f"n must satisfy 1 <= n <= {MAX_N}")
            size = math.factorial(n)
            sigma_idx = int(payload.get("sigma", 1))
            tau_idx = int(payload.get("tau", 1))
            if not 1 <= sigma_idx <= size or not 1 <= tau_idx <= size:
                raise ValueError(f"Permutation indices must be between 1 and {size}")
            tuples = permutation_tuples(n)
            sigma = tuples[sigma_idx - 1]
            tau = tuples[tau_idx - 1]
            result = compose(sigma, tau)
            result_index = tuples.index(tuple(result)) + 1
            self._send_json(
                {
                    "n": n,
                    "sigma": permutation_record(sigma_idx, sigma),
                    "tau": permutation_record(tau_idx, tau),
                    "result": permutation_record(result_index, result),
                    "reading": "apply tau first, then sigma",
                }
            )
            return

        if path == "/api/generated-subgroup":
            n = int(payload.get("n", 4))
            if not 1 <= n <= MAX_GENERATED_SUBGROUP_N:
                raise ValueError(
                    f"Generated-subgroup mode is capped at n <= {MAX_GENERATED_SUBGROUP_N}"
                )
            raw_indices = payload.get("generators", [])
            if not isinstance(raw_indices, list) or not raw_indices:
                raise ValueError("generators must be a non-empty list of indices")
            tuples = permutation_tuples(n)
            size = len(tuples)
            indices = []
            for raw in raw_indices:
                idx = int(raw)
                if not 1 <= idx <= size:
                    raise ValueError(f"Generator indices must be between 1 and {size}")
                if idx not in indices:
                    indices.append(idx)
            generators = [tuples[idx - 1] for idx in indices]
            subgroup = generate_subgroup(generators, n)
            ambient = generate_permutations(n)
            self._send_json(
                {
                    "n": n,
                    "generator_indices": indices,
                    "order": len(subgroup),
                    "normal_in_sn": is_normal_subgroup(subgroup, ambient),
                    "members": [
                        {
                            "one_line": one_line_notation(p),
                            "cycles": cycle_notation(p),
                        }
                        for p in subgroup
                    ],
                }
            )
            return

        raise ValueError("Unknown API endpoint")


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ExplorerHandler)
    print(f"S_n Explorer Web running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
