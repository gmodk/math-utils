"""One-command launcher that creates an isolated Python environment on first run."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parent
ENVIRONMENT = ROOT / ".venv"


def environment_python() -> Path:
    if os.name == "nt":
        return ENVIRONMENT / "Scripts" / "python.exe"
    return ENVIRONMENT / "bin" / "python"


def main() -> None:
    if sys.prefix == sys.base_prefix:
        executable = environment_python()
        if not executable.exists():
            print("Creating the local Python environment…")
            venv.EnvBuilder(with_pip=True).create(ENVIRONMENT)
        os.execv(str(executable), [str(executable), str(Path(__file__).resolve()), *sys.argv[1:]])

    try:
        import fastapi  # noqa: F401
        import networkx  # noqa: F401
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print("Installing the numerical engine (first run only)…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])

    from app import main as run_application

    run_application()


if __name__ == "__main__":
    main()
