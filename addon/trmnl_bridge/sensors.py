"""Generic sensor / entity readings for a feed (the non-weather buckets)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .formatting import num
from .ha import HAError, get_state

if TYPE_CHECKING:
    from .settings import Settings


def build_sensor_list(settings: "Settings", feed: dict, key: str,
                      errors: list[str]) -> list[dict]:
    """Build a list of {label, value, unit, ...} from a feed's section.

    `key` is "sensors" or "entities" — same shape, two named buckets so the
    template can lay them out as distinct groups.
    """
    out = []
    for entry in feed.get(key, []):
        entity_id = entry.get("entity_id")
        if not entity_id:
            continue
        try:
            st = get_state(settings, entity_id)
        except HAError as e:
            errors.append(f"{key}/{entity_id}: {e}")
            out.append({
                "entity_id": entity_id,
                "label": entry.get("label") or entity_id,
                "value": None,
                "unit": entry.get("unit", ""),
                "available": False,
            })
            continue
        attrs = st.get("attributes", {})
        raw_state = st.get("state")
        coerced = num(raw_state)
        out.append({
            "entity_id": entity_id,
            "label": entry.get("label")
            or attrs.get("friendly_name") or entity_id,
            "value": coerced if coerced is not None else raw_state,
            "unit": entry.get("unit", attrs.get("unit_of_measurement", "")),
            "device_class": attrs.get("device_class"),
            "available": raw_state not in (None, "unknown", "unavailable"),
        })
    return out
