#!/usr/bin/env python3
"""TRMNL HA Bridge — entrypoint.

A thin launcher; the implementation lives in the ``trmnl_bridge`` package
beside this file (core HA access + payload assembly, the JSON feed server, and
the Ingress config panel). See ``trmnl_bridge/__init__.py`` for the overview.

The feed-serving core is stdlib-only; PyYAML is used only to read the optional
``templates.yaml`` panel metadata (and is imported lazily). Runs both as a Home
Assistant add-on (``python3 /app/bridge.py``) and standalone.
"""

from __future__ import annotations

import os
import sys

# Ensure the sibling package is importable regardless of the current working
# directory (e.g. when launched as `python3 /app/bridge.py`).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trmnl_bridge.cli import main  # noqa: E402  (after sys.path setup)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
