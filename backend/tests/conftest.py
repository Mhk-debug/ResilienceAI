"""
Shared pytest configuration.

The test suite mixes two import styles:
  * ``from backend.xxx import ...``  (requires the project ROOT on sys.path)
  * ``from main import app`` etc.    (requires the BACKEND dir on sys.path)

This conftest puts both on sys.path so any test can be run from the
project root or from the backend directory.
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

for _p in (BACKEND_DIR, ROOT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)