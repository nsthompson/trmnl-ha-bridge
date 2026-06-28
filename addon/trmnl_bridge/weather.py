"""Current-conditions and forecast assembly for a weather feed."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .formatting import date_label, num, titleize, weekday
from .ha import HAError, get_state, ha_request

if TYPE_CHECKING:
    from .settings import Settings

# Human-readable labels for Home Assistant weather conditions.
# https://www.home-assistant.io/integrations/weather/#condition-mapping
CONDITION_LABELS = {
    "clear-night": "Clear",
    "cloudy": "Cloudy",
    "exceptional": "Exceptional",
    "fog": "Fog",
    "hail": "Hail",
    "lightning": "Lightning",
    "lightning-rainy": "Thunderstorms",
    "partlycloudy": "Partly Cloudy",
    "pouring": "Heavy Rain",
    "rainy": "Rain",
    "snowy": "Snow",
    "snowy-rainy": "Sleet",
    "sunny": "Sunny",
    "windy": "Windy",
    "windy-variant": "Windy",
}


def build_weather(settings: "Settings", feed: dict, errors: list[str]) -> dict:
    entity_id = feed.get("weather_entity")
    if not entity_id:
        return {}
    try:
        st = get_state(settings, entity_id)
    except HAError as e:
        errors.append(f"weather: {e}")
        return {}
    attrs = st.get("attributes", {})
    condition = st.get("state")
    weather = {
        "entity_id": entity_id,
        "condition": condition,
        "condition_label": CONDITION_LABELS.get(condition, titleize(condition)),
        "temperature": num(attrs.get("temperature")),
        "temperature_unit": attrs.get("temperature_unit", "°"),
        "apparent_temperature": num(attrs.get("apparent_temperature")),
        "humidity": num(attrs.get("humidity")),
        "pressure": num(attrs.get("pressure")),
        "pressure_unit": attrs.get("pressure_unit", ""),
        "wind_speed": num(attrs.get("wind_speed")),
        "wind_speed_unit": attrs.get("wind_speed_unit", ""),
        "wind_bearing": attrs.get("wind_bearing"),
        "friendly_name": attrs.get("friendly_name"),
    }

    # Some weather integrations (e.g. WeatherFlow Forecast) don't expose an
    # apparent ("feels like") temperature. Let a separate sensor supply it.
    feels_entity = feed.get("feels_like_entity")
    if feels_entity:
        try:
            fst = get_state(settings, feels_entity)
            fval = num(fst.get("state"))
            if fval is not None:
                weather["apparent_temperature"] = fval
        except HAError as e:
            errors.append(f"feels_like: {e}")
    return weather


def build_forecast(settings: "Settings", feed: dict, errors: list[str]) -> list[dict]:
    entity_id = feed.get("weather_entity")
    if not entity_id:
        return []
    forecast_type = feed.get("forecast_type", "daily")
    limit = int(feed.get("forecast_days", 4))
    try:
        result = ha_request(
            settings,
            "/api/services/weather/get_forecasts?return_response",
            method="POST",
            body={"type": forecast_type, "entity_id": entity_id},
        )
    except HAError as e:
        errors.append(f"forecast: {e}")
        return []

    service_response = (result or {}).get("service_response", {})
    entity_block = service_response.get(entity_id, {})
    raw = entity_block.get("forecast", [])

    out = []
    for item in raw[:limit]:
        dt = item.get("datetime")
        out.append({
            "datetime": dt,
            "day": weekday(dt),
            "date_label": date_label(dt),
            "condition": item.get("condition"),
            "condition_label": CONDITION_LABELS.get(
                item.get("condition"), titleize(item.get("condition"))),
            "high": num(item.get("temperature")),
            "low": num(item.get("templow")),
            "precipitation": num(item.get("precipitation")),
            "precipitation_probability": num(
                item.get("precipitation_probability")),
        })
    return out
