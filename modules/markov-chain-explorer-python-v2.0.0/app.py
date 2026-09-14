from __future__ import annotations

import argparse
import os
from threading import Timer
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Markov Chain Explorer Python edition.")
    parser.add_argument("--host", default=os.getenv("MARKOV_EXPLORER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MARKOV_EXPLORER_PORT", "8765")))
    parser.add_argument("--reload", action="store_true", help="Reload Python source automatically during development.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the explorer in the default browser.")
    arguments = parser.parse_args()
    if not arguments.no_browser and not arguments.reload:
        browser_host = "127.0.0.1" if arguments.host in {"0.0.0.0", "::"} else arguments.host
        Timer(1.0, lambda: webbrowser.open(f"http://{browser_host}:{arguments.port}")).start()
    uvicorn.run("backend.api:app", host=arguments.host, port=arguments.port, reload=arguments.reload)


if __name__ == "__main__":
    main()
