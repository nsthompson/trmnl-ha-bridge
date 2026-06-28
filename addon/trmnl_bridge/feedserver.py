"""The public JSON feed server — what a TRMNL/Terminus device polls.

Serves one cached JSON document per feed at ``/feeds/<slug>.json`` (plus an
index, a health check, and a ``/trmnl.json`` alias for the first feed). This is
the data plane; the configuration UI lives in :mod:`trmnl_bridge.panel`.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING

from .payload import build_feed_payload

if TYPE_CHECKING:
    from .settings import Settings


class Cache:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self._lock = threading.Lock()
        self._value: dict | None = None
        self._fetched_at = 0.0

    def get(self, producer) -> dict:
        with self._lock:
            age = time.monotonic() - self._fetched_at
            if self._value is None or age >= self.ttl:
                self._value = producer()
                self._fetched_at = time.monotonic()
            return self._value


def make_handler(settings: "Settings"):
    caches: dict[str, Cache] = {}
    clock = threading.Lock()

    def feed_payload(slug: str, fbs: dict) -> dict:
        with clock:
            cache = caches.get(slug)
            if cache is None:
                cache = caches[slug] = Cache(settings.cache_ttl)
        return cache.get(lambda: build_feed_payload(settings, fbs[slug]))

    class Handler(BaseHTTPRequestHandler):
        server_version = "trmnl-ha-bridge/1.0"

        def _send(self, code: int, obj: object) -> None:
            body = json.dumps(obj, indent=2).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _index(self, fbs: dict) -> dict:
            return {
                "service": "trmnl-ha-bridge",
                "mode": settings.mode,
                "feeds": [
                    {"slug": s, "url": f"/feeds/{s}.json",
                     "location": fbs[s].get("location", "")}
                    for s in fbs
                ],
            }

        def do_GET(self):  # noqa: N802 (stdlib naming)
            # Pick up edits made in the config panel without a restart.
            if settings.reload_if_changed():
                with clock:
                    caches.clear()
            fbs = {f["slug"]: f for f in settings.feeds}
            path = self.path.split("?")[0]
            try:
                if path in ("/", "/index.json"):
                    self._send(200, self._index(fbs))
                elif path == "/health":
                    self._send(200, {"status": "ok", "feeds": len(fbs)})
                elif path.startswith("/feeds/") and path.endswith(".json"):
                    slug = path[len("/feeds/"):-len(".json")]
                    if slug in fbs:
                        self._send(200, feed_payload(slug, fbs))
                    else:
                        self._send(404, {"error": f"unknown feed '{slug}'",
                                         "available": list(fbs)})
                elif path == "/trmnl.json" and fbs:
                    first = next(iter(fbs))
                    self._send(200, feed_payload(first, fbs))
                else:
                    self._send(404, {"error": "not found"})
            except Exception as e:  # never 500 a device's poll
                self._send(200, {"errors": [f"bridge: {e}"], "weather": {},
                                 "forecast": [], "sensors": [],
                                 "entities": []})

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(),
                                            fmt % args))

    return Handler
