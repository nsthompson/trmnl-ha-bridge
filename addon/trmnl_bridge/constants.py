"""Filesystem paths, network constants, and access control for the bridge."""

from __future__ import annotations

import os

# Directory layout. This package lives at <APP_DIR>/trmnl_bridge/; the bundled
# Liquid templates and the entrypoint bridge.py sit beside it in <APP_DIR>
# (Docker: /app; dev: the addon/ folder).
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(PACKAGE_DIR)
PANEL_ASSETS_DIR = os.path.join(PACKAGE_DIR, "panel_assets")

OPTIONS_PATH = "/data/options.json"     # written by the HA Supervisor
FEEDS_STATE_PATH = "/data/feeds.json"   # feed config managed by the Ingress panel
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")  # bundled Liquid views

# Folders scanned for templates: the bundled set plus an optional
# /data/templates overlay you can drop your own (non-weather) templates into.
TEMPLATE_DIRS = [TEMPLATES_DIR,
                 os.path.join(os.path.dirname(OPTIONS_PATH), "templates")]

INGRESS_PORT = 8099                     # HA add-on Ingress default port
# Only the Supervisor (and localhost, for dev) may reach the config panel/API.
INGRESS_ALLOWED = {"172.30.32.2", "127.0.0.1", "::1", "::ffff:127.0.0.1"}
