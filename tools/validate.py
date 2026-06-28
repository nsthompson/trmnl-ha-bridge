#!/usr/bin/env python3
"""Validate a TRMNL HA Bridge feed payload (live or sample).

Checks the document the templates depend on and reports problems before you
render: missing/empty sections, stale data, unavailable entities, AQI out of
range, and any errors the bridge itself reported. Exits non-zero on a hard
failure (malformed payload) so it can gate CI / scripts.

Usage: validate.py <feed.json> [feed-name]
"""
import json
import sys
from datetime import datetime, timezone

path = sys.argv[1]
try:
    data = json.loads(open(path, encoding="utf-8").read())
except (OSError, json.JSONDecodeError) as exc:
    print(f"FAIL: could not read/parse {path}: {exc}")
    sys.exit(2)

name = sys.argv[2] if len(sys.argv) > 2 else (data.get("slug") or "feed")
warns: list[str] = []
errs: list[str] = []

if not isinstance(data, dict):
    print(f"FAIL: feed payload is not a JSON object (got {type(data).__name__})")
    sys.exit(2)

# --- structure ---------------------------------------------------------------
for key in ("weather", "forecast", "sensors", "entities"):
    if key not in data:
        errs.append(f"missing top-level key '{key}'")

# --- freshness ---------------------------------------------------------------
age = ""
ga = data.get("generated_at")
if ga:
    try:
        dt = datetime.fromisoformat(str(ga).replace("Z", "+00:00"))
        secs = (datetime.now(timezone.utc) - dt).total_seconds()
        mins, rem = divmod(int(abs(secs)), 60)
        age = f"{mins}m{rem}s " + ("in the future" if secs < 0 else "ago")
        if secs > 3600:
            warns.append(f"data is stale ({age}) — is the bridge polling?")
        elif secs < -120:
            warns.append(f"generated_at is {age} "
                         "(clock skew between this host and HA?)")
    except ValueError:
        warns.append("generated_at is not a valid timestamp")
else:
    warns.append("no generated_at field")

# --- weather -----------------------------------------------------------------
wx = data.get("weather") or {}
if not wx:
    warns.append("weather is empty (no weather_entity set, or the fetch failed)")
else:
    if wx.get("temperature") is None:
        warns.append("weather.temperature is missing/null")
    if not wx.get("condition"):
        warns.append("weather.condition is missing (icons will fall back)")

# --- forecast ----------------------------------------------------------------
fc = data.get("forecast") or []
if not fc:
    warns.append("forecast is empty (entity may not support the forecast type)")

# --- air quality -------------------------------------------------------------
aq = data.get("air_quality") or {}
if aq:
    if aq.get("available"):
        v = aq.get("value")
        if not isinstance(v, (int, float)) or not (0 <= v <= 500):
            warns.append(f"AQI value out of 0–500 range: {v!r}")
        if aq.get("gauge_angle") is None:
            errs.append("air_quality.gauge_angle missing (gauge can't render)")
        if not aq.get("gauge_ticks"):
            warns.append("air_quality.gauge_ticks missing (no dial ticks)")
    else:
        warns.append("air_quality present but the AQI entity is unavailable")

# --- entity availability -----------------------------------------------------
for grp in ("sensors", "entities"):
    items = data.get(grp) or []
    for s in items:
        if not s.get("available", True):
            warns.append(f"{grp[:-1]} '{s.get('label') or s.get('entity_id')}' "
                         f"is unavailable (shows as —)")

# --- bridge-reported errors --------------------------------------------------
for er in data.get("errors", []) or []:
    errs.append(f"bridge reported: {er}")

# --- report ------------------------------------------------------------------
print(f"feed: {name}")
if ga:
    print(f"  generated_at : {ga}" + (f"  ({age})" if age else ""))
if wx:
    print(f"  weather      : {wx.get('condition')} "
          f"{wx.get('temperature')}{wx.get('temperature_unit', '')}")
print(f"  forecast     : {len(fc)} period(s)")
if aq:
    print(f"  air_quality  : {aq.get('value')} {aq.get('category_short')} "
          f"(gauge {aq.get('gauge_angle')})")
print(f"  sensors      : {len(data.get('sensors') or [])} | "
      f"entities: {len(data.get('entities') or [])}")
for m in warns:
    print(f"  WARN: {m}")
for m in errs:
    print(f"  FAIL: {m}")
status = "FAIL" if errs else ("WARN" if warns else "OK")
print(f"RESULT: {status}  ({len(errs)} error(s), {len(warns)} warning(s))")
sys.exit(1 if errs else 0)
