@echo off
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -e .
python app.py
