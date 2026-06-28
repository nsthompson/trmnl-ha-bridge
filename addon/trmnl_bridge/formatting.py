"""Stateless value helpers: numeric coercion, slugs, and date/label formatting.

These have no dependency on Home Assistant or configuration, so every other
module can lean on them without creating import cycles.
"""

from __future__ import annotations

from datetime import datetime


def num(value: object) -> float | int | None:
    """Best-effort numeric coercion; HA state values are strings."""
    if value in (None, "", "unknown", "unavailable"):
        return None
    try:
        f = float(value)
        return int(f) if f.is_integer() else round(f, 1)
    except (TypeError, ValueError):
        return None


def titleize(value: object) -> str:
    if not value:
        return ""
    return str(value).replace("-", " ").replace("_", " ").title()


def slugify(value: object) -> str:
    text = str(value or "").strip().lower()
    out = "".join(c if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "feed"


def parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def weekday(value: object) -> str:
    dt = parse_dt(value)
    return dt.strftime("%a") if dt else ""


def date_label(value: object) -> str:
    # Build "27 Jun" without the glibc-only %-d (musl/Alpine lacks it).
    dt = parse_dt(value)
    return f"{dt.day} {dt.strftime('%b')}" if dt else ""


def format_updated(now: datetime) -> str:
    """Friendly local 'last updated' label, e.g. 'Jun 27, 3:55 PM'. Converts the
    UTC build time to the add-on's local timezone (set by the Supervisor)."""
    local = now.astimezone()
    hour12 = local.strftime("%I").lstrip("0") or "12"
    return (f"{local.strftime('%b')} {local.day}, "
            f"{hour12}:{local.strftime('%M %p')}")
