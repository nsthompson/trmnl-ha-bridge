"""Command-line entry point and the runtime composition root (``serve``)."""

from __future__ import annotations

import json
import sys
import threading
from http.server import ThreadingHTTPServer

from .constants import INGRESS_PORT
from .feedserver import make_handler
from .ha import HAError, ha_request
from .panel import make_ingress_handler
from .payload import build_feed_payload
from .settings import Settings


def serve(settings: Settings) -> None:
    # Config panel (Ingress) — best-effort; the feed server is what matters.
    try:
        ingress = ThreadingHTTPServer(("0.0.0.0", INGRESS_PORT),
                                      make_ingress_handler(settings))
        threading.Thread(target=ingress.serve_forever, daemon=True).start()
        print(f"[trmnl-ha-bridge] config panel (Ingress) on :{INGRESS_PORT}",
              file=sys.stderr)
    except OSError as e:
        print(f"[trmnl-ha-bridge] config panel unavailable: {e}",
              file=sys.stderr)

    httpd = ThreadingHTTPServer(("0.0.0.0", settings.port),
                                make_handler(settings))
    slugs = ", ".join(f["slug"] for f in settings.feeds) or "(none)"
    print(f"[trmnl-ha-bridge] mode={settings.mode} port={settings.port} "
          f"cache={settings.cache_ttl}s feeds=[{slugs}]", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[trmnl-ha-bridge] shutting down", file=sys.stderr)
        httpd.shutdown()


def main(argv: list[str]) -> int:
    settings = Settings()

    if "--check" in argv:
        problems = settings.validate()
        if problems:
            print("config problems:\n  - " + "\n  - ".join(problems),
                  file=sys.stderr)
            return 1
        try:
            ha_request(settings, "/api/")
            print(f"OK: reached Home Assistant ({settings.mode} mode) "
                  f"at {settings.ha_url}")
            for f in settings.feeds:
                print(f"  feed '{f['slug']}': weather="
                      f"{f.get('weather_entity') or '-'}, "
                      f"{len(f.get('sensors', []))} sensors, "
                      f"{len(f.get('entities', []))} entities")
            return 0
        except HAError as e:
            print(f"FAILED to reach Home Assistant: {e}", file=sys.stderr)
            return 1

    # Block only on a missing HA connection; an empty feed list is fine —
    # the user can add feeds in the config panel, which applies them live.
    problems = settings.validate()
    fatal = [p for p in problems if "feed" not in p.lower()]
    if fatal:
        print("config problems:\n  - " + "\n  - ".join(fatal), file=sys.stderr)
        return 1
    for p in problems:
        if p not in fatal:
            print(f"[trmnl-ha-bridge] note: {p} (add feeds in the panel)",
                  file=sys.stderr)

    if "--once" in argv:
        out = {f["slug"]: build_feed_payload(settings, f)
               for f in settings.feeds}
        print(json.dumps(out, indent=2))
        return 0

    serve(settings)
    return 0
