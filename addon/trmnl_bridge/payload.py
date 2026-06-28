"""Per-feed payload assembly — the JSON shape a Terminus extension consumes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .aqi import build_air_quality
from .formatting import format_updated
from .sensors import build_sensor_list
from .weather import build_forecast, build_weather

if TYPE_CHECKING:
    from .settings import Settings


def build_feed_payload(settings: "Settings", feed: dict) -> dict:
    errors: list[str] = []
    # A "sensors" feed is generic — no weather/forecast/AQI, just readings.
    is_weather = feed.get("type", "weather") != "sensors"
    now = datetime.now(timezone.utc)
    return {
        "slug": feed["slug"],
        "type": feed.get("type", "weather"),
        "generated_at": now.isoformat(timespec="seconds"),
        "generated_label": format_updated(now),
        "location": feed.get("location", ""),
        "weather": build_weather(settings, feed, errors) if is_weather else {},
        "forecast": build_forecast(settings, feed, errors) if is_weather else [],
        "air_quality": build_air_quality(settings, feed, errors) if is_weather else {},
        "sensors": build_sensor_list(settings, feed, "sensors", errors),
        "entities": build_sensor_list(settings, feed, "entities", errors),
        "errors": errors,
    }
