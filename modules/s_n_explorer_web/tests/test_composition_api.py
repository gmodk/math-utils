"""HTTP contract for the additive composition trace."""

import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, urlopen

from modules.s_n_explorer_web.app import ExplorerHandler


def test_compose_response_keeps_existing_fields_and_adds_trace():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ExplorerHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/compose",
            data=json.dumps({"n": 3, "sigma": 4, "tau": 2}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            assert response.status == 200
            payload = json.load(response)
        assert {"n", "sigma", "tau", "result", "reading", "trace"} <= payload.keys()
        assert payload["reading"] == "apply tau first, then sigma"
        assert payload["sigma"]["permutation"] == [1, 2, 0]
        assert payload["tau"]["permutation"] == [0, 2, 1]
        assert payload["result"]["permutation"] == [1, 0, 2]
        assert payload["trace"] == [
            {"input": 1, "after_tau": 1, "result": 2},
            {"input": 2, "after_tau": 3, "result": 1},
            {"input": 3, "after_tau": 2, "result": 3},
        ]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
