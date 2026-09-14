#!/usr/bin/env sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python app.py
