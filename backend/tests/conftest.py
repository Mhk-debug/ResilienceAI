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

# ── Keep the retrieval tests hermetic ─────────────────────────────────
# The RAG tests load all-MiniLM-L6-v2 via sentence-transformers, whose model
# lookup goes through httpx. In a shell that exports a SOCKS proxy, httpx
# raises ImportError when "socksio" is absent, and an offline machine cannot
# download the weights — either way the retrieval tests silently drop out of
# the run. Load from the local cache and ignore ambient proxy settings so the
# suite means the same thing on every machine.
for _proxy_var in ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy",
                   "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy"):
    os.environ.pop(_proxy_var, None)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
