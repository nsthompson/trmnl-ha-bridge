"""The Ingress configuration panel — the add-on's web UI.

This is the control plane: a small HTTP server (reachable only from the
Supervisor / localhost) that backs the panel with three JSON endpoints
(entities, templates, config) and serves the static UI from ``panel_assets/``.
The presentation — HTML, CSS, JS — lives entirely in those asset files, not in
Python; only ``index.html`` is templated, to inject the Ingress base path.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING

from .constants import INGRESS_ALLOWED, PANEL_ASSETS_DIR
from .ha import HAError, ha_entities
from .templates import load_templates

if TYPE_CHECKING:
    from .settings import Settings

# Static assets served behind Ingress. index.html is templated (its __BASE__
# placeholder becomes the Ingress base path); the rest are byte-for-byte.
_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".html": "text/html; charset=utf-8",
}
_STATIC_ASSETS = {"/panel.css": "panel.css", "/panel.js": "panel.js"}

_asset_cache: dict[str, str] = {}


def _asset(name: str) -> str:
    """Read a panel asset (cached — the files are static in the image)."""
    if name not in _asset_cache:
        with open(os.path.join(PANEL_ASSETS_DIR, name),
                  "r", encoding="utf-8") as fh:
            _asset_cache[name] = fh.read()
    return _asset_cache[name]


def make_ingress_handler(settings: "Settings"):
    class Ingress(BaseHTTPRequestHandler):
        server_version = "trmnl-ha-bridge-ui/1.0"

        def _allowed(self) -> bool:
            return self.client_address[0] in INGRESS_ALLOWED

        def _json(self, code: int, obj: object) -> None:
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _asset_response(self, text: str, content_type: str) -> None:
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if not self._allowed():
                self.send_response(403)
                self.end_headers()
                return
            path = self.path.split("?")[0]
            if path == "/api/entities":
                try:
                    self._json(200, {"entities": ha_entities(settings)})
                except HAError as e:
                    self._json(200, {"entities": [], "error": str(e)})
            elif path == "/api/templates":
                self._json(200, {"templates": load_templates()})
            elif path == "/api/config":
                self._json(200, {"feeds": settings.feeds, "mode": settings.mode})
            elif path in _STATIC_ASSETS:
                fname = _STATIC_ASSETS[path]
                ctype = _CONTENT_TYPES.get(os.path.splitext(fname)[1],
                                           "text/plain; charset=utf-8")
                self._asset_response(_asset(fname), ctype)
            else:
                base = self.headers.get("X-Ingress-Path", "")
                base = (base + "/") if base else ""
                html = _asset("index.html").replace("__BASE__", base)
                self._asset_response(html, _CONTENT_TYPES[".html"])

        def do_POST(self):  # noqa: N802
            if not self._allowed():
                self.send_response(403)
                self.end_headers()
                return
            if self.path.split("?")[0] != "/api/config":
                self._json(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0") or 0)
                payload = json.loads(self.rfile.read(length) or b"{}")
                settings.save_feeds(payload.get("feeds", []))
                self._json(200, {"ok": True, "feeds": settings.feeds})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})

        def log_message(self, fmt, *args):
            pass

    return Ingress
