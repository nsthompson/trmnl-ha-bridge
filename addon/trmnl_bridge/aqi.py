"""Air Quality Index: AirNow category mapping + dial geometry + feed block.

The device renders FILLED shapes only — no strokes, and SVG transforms aren't
relied upon — so the gauge geometry here computes concrete coordinates (a
filled triangular needle and filled tick dots) for templates that want a dial.
The current templates use the level-of-concern faces instead, but the gauge
fields are still emitted for backwards compatibility / alternative layouts.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .formatting import num
from .ha import HAError, get_state

if TYPE_CHECKING:
    from .settings import Settings

# US EPA Air Quality Index categories (level of concern).
# https://www.airnow.gov/aqi/aqi-basics/  -> (upper_bound, name, short, level)
AQI_CATEGORIES = [
    (50, "Good", "Good", 1),
    (100, "Moderate", "Moderate", 2),
    (150, "Unhealthy for Sensitive Groups", "Sensitive", 3),
    (200, "Unhealthy", "Unhealthy", 4),
    (300, "Very Unhealthy", "Very Unhealthy", 5),
    (500, "Hazardous", "Hazardous", 6),
]


def aqi_category(value: int) -> tuple[str, str, int]:
    """Map an AQI number to its AirNow (name, short_name, level 1-6)."""
    for upper, name, short, level in AQI_CATEGORIES:
        if value <= upper:
            return name, short, level
    return "Hazardous", "Hazardous", 6  # anything above 500


# AQI gauge geometry. Canvas is the template's viewBox "0 0 100 60"; hub at
# (50, 54); value 0 -> needle left, 250 -> up, 500 -> right. Thresholds match
# AQI_CATEGORIES.
AQI_GAUGE_MAX = 500
AQI_GAUGE_TICKS = [50, 100, 150, 200, 300]
_GAUGE_HUB = (50.0, 54.0)
_GAUGE_NEEDLE_LEN = 36.0
_GAUGE_NEEDLE_HALFWIDTH = 3.0
_GAUGE_TICK_RADIUS = 40.0


def _aqi_gauge_angle(value: float) -> float:
    clamped = max(0, min(AQI_GAUGE_MAX, value))
    return round(clamped / AQI_GAUGE_MAX * 180 - 90, 2)


def _gauge_dir(value: float) -> tuple[float, float]:
    """Unit direction for an AQI value (0deg = straight up)."""
    rad = math.radians(_aqi_gauge_angle(value))
    return math.sin(rad), -math.cos(rad)


def _aqi_gauge_needle(value: float) -> str:
    """Filled-triangle needle as an SVG <path> `d` string (device renders
    fills/paths, not polygons or transforms)."""
    cx, cy = _GAUGE_HUB
    dx, dy = _gauge_dir(value)
    px, py = -dy, dx  # perpendicular to the needle
    tip = (cx + _GAUGE_NEEDLE_LEN * dx, cy + _GAUGE_NEEDLE_LEN * dy)
    b1 = (cx + _GAUGE_NEEDLE_HALFWIDTH * px, cy + _GAUGE_NEEDLE_HALFWIDTH * py)
    b2 = (cx - _GAUGE_NEEDLE_HALFWIDTH * px, cy - _GAUGE_NEEDLE_HALFWIDTH * py)
    (tx, ty), (x1, y1), (x2, y2) = tip, b1, b2
    return (f"M{round(tx, 2)} {round(ty, 2)}L{round(x1, 2)} {round(y1, 2)}"
            f"L{round(x2, 2)} {round(y2, 2)}Z")


def _aqi_gauge_tick_points(ticks: list[int]) -> list[dict]:
    """Tick centre points on the dial rim. The template draws each as a filled
    disc <path> (the device mis-positions <circle>)."""
    cx, cy = _GAUGE_HUB
    pts = []
    for t in ticks:
        dx, dy = _gauge_dir(t)
        pts.append({"x": round(cx + _GAUGE_TICK_RADIUS * dx, 2),
                    "y": round(cy + _GAUGE_TICK_RADIUS * dy, 2)})
    return pts


def build_air_quality(settings: "Settings", feed: dict, errors: list[str]) -> dict:
    entity_id = feed.get("aqi_entity")
    if not entity_id:
        return {}
    try:
        st = get_state(settings, entity_id)
    except HAError as e:
        errors.append(f"aqi: {e}")
        return {"entity_id": entity_id, "available": False, "value": None}
    attrs = st.get("attributes", {})
    value = num(st.get("state"))
    if value is None:
        return {"entity_id": entity_id, "available": False, "value": None}
    v = int(round(value))
    name, short, level = aqi_category(v)
    return {
        "entity_id": entity_id,
        "available": True,
        "value": v,
        "category": name,
        "category_short": short,
        "level": level,
        "unit": attrs.get("unit_of_measurement", "AQI"),
        "gauge_angle": _aqi_gauge_angle(v),
        "gauge_needle": _aqi_gauge_needle(v),
        "gauge_ticks": _aqi_gauge_tick_points(AQI_GAUGE_TICKS),
    }
