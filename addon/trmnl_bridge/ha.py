"""Home Assistant REST client.

A thin wrapper over the HA REST API that works identically in add-on mode (via
the Supervisor proxy) and standalone mode (direct to ``$HA_URL``) — the
difference is entirely captured by ``Settings.ha_url`` / ``Settings.ha_token``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import Settings


class HAError(Exception):
    pass


def ha_request(settings: "Settings", path: str, method: str = "GET",
               body: dict | None = None) -> object:
    """Call the Home Assistant REST API. Returns parsed JSON (or None).

    `path` is the core path beginning with /api/... — in add-on mode it is
    transparently proxied (base http://supervisor/core), in standalone mode it
    hits $HA_URL directly. Both append the same /api/... path.
    """
    url = f"{settings.ha_url}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {settings.ha_token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=settings.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise HAError(f"{method} {path} -> HTTP {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise HAError(f"{method} {path} -> {e.reason}") from e
    except (TimeoutError, json.JSONDecodeError) as e:
        raise HAError(f"{method} {path} -> {e}") from e


def get_state(settings: "Settings", entity_id: str) -> dict:
    result = ha_request(settings, f"/api/states/{entity_id}")
    if not isinstance(result, dict):
        raise HAError(f"unexpected state payload for {entity_id}")
    return result


def ha_entities(settings: "Settings") -> list[dict]:
    """Every HA entity as {entity_id, name, domain, unit} for the picker UI."""
    result = ha_request(settings, "/api/states")
    out = []
    for st in result or []:
        if not isinstance(st, dict):
            continue
        eid = st.get("entity_id") or ""
        attrs = st.get("attributes", {})
        out.append({
            "entity_id": eid,
            "name": attrs.get("friendly_name") or eid,
            "domain": eid.split(".")[0] if "." in eid else "",
            "unit": attrs.get("unit_of_measurement", ""),
        })
    out.sort(key=lambda e: (e["domain"], e["name"].lower()))
    return out
