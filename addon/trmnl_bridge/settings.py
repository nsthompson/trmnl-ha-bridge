"""Resolved runtime configuration, independent of where it came from."""

from __future__ import annotations

import json
import os
import threading

from .constants import FEEDS_STATE_PATH, OPTIONS_PATH
from .formatting import slugify


def env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


class Settings:
    """Resolved runtime configuration, independent of where it came from."""

    def __init__(self) -> None:
        options = self._load_options()

        supervisor_token = env("SUPERVISOR_TOKEN")
        if supervisor_token:
            # Add-on mode: talk to Core through the Supervisor proxy.
            self.ha_url = "http://supervisor/core"
            self.ha_token = supervisor_token
            self.mode = "addon"
        else:
            # Standalone mode.
            self.ha_url = (env("HA_URL") or "").rstrip("/")
            self.ha_token = env("HA_TOKEN") or ""
            self.mode = "standalone"

        self.port = int(options.get("port") or env("PORT", "8080"))
        self.cache_ttl = int(options.get("cache_ttl")
                             or env("CACHE_TTL", "300"))
        self.timeout = int(options.get("request_timeout")
                           or env("HA_TIMEOUT", "10"))
        self.log_level = (options.get("log_level")
                          or env("LOG_LEVEL", "info")).lower()
        self.options = options
        self._feeds_mtime: float | None = None
        self._lock = threading.Lock()
        self.feeds = self._load_feeds(options)

    def _load_options(self) -> dict:
        """Add-on options.json, or a standalone CONFIG_PATH file, or {}."""
        if os.path.exists(OPTIONS_PATH):
            with open(OPTIONS_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        config_path = env("CONFIG_PATH", "config.json")
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return {}

    def _load_feeds(self, options: dict) -> list[dict]:
        """Feeds come from FEEDS_STATE_PATH (managed by the config panel) when
        it exists, else from add-on options. Seeds the state file on first run
        so the panel has the options' feeds to start from."""
        raw = None
        if os.path.exists(FEEDS_STATE_PATH):
            try:
                with open(FEEDS_STATE_PATH, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                self._feeds_mtime = os.path.getmtime(FEEDS_STATE_PATH)
            except (OSError, json.JSONDecodeError):
                raw = None
        if raw is None:
            raw = options.get("feeds")
            self._seed_feeds_file(raw)
        return self._normalize_feeds(raw)

    def _seed_feeds_file(self, raw) -> None:
        try:
            parent = os.path.dirname(FEEDS_STATE_PATH)
            if not os.path.exists(FEEDS_STATE_PATH) and os.path.isdir(parent):
                with open(FEEDS_STATE_PATH, "w", encoding="utf-8") as fh:
                    json.dump(raw or [], fh, indent=2)
                self._feeds_mtime = os.path.getmtime(FEEDS_STATE_PATH)
        except OSError:
            pass

    def reload_if_changed(self) -> bool:
        """Reload feeds if the panel rewrote the state file."""
        try:
            if os.path.exists(FEEDS_STATE_PATH):
                m = os.path.getmtime(FEEDS_STATE_PATH)
                if m != self._feeds_mtime:
                    with open(FEEDS_STATE_PATH, "r", encoding="utf-8") as fh:
                        raw = json.load(fh)
                    with self._lock:
                        self.feeds = self._normalize_feeds(raw)
                        self._feeds_mtime = m
                    return True
        except (OSError, json.JSONDecodeError):
            pass
        return False

    def save_feeds(self, raw_feeds: list) -> None:
        """Persist feeds from the panel and apply them live."""
        with open(FEEDS_STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(raw_feeds, fh, indent=2)
        with self._lock:
            self.feeds = self._normalize_feeds(raw_feeds)
            self._feeds_mtime = os.path.getmtime(FEEDS_STATE_PATH)

    @staticmethod
    def _normalize_feeds(raw) -> list[dict]:
        """Accept either a `feeds` list or a single legacy top-level feed.

        Ensures every feed has a unique, URL-safe slug and sane defaults.
        """
        if not raw:
            return []
        feeds = []
        seen = set()
        for idx, item in enumerate(raw):
            slug = slugify(item.get("slug") or item.get("location") or f"feed{idx + 1}")
            # Guarantee uniqueness even if two feeds slugify the same.
            base, n = slug, 2
            while slug in seen:
                slug = f"{base}-{n}"
                n += 1
            seen.add(slug)
            ftype = "sensors" if item.get("type") == "sensors" else "weather"
            feeds.append({
                "slug": slug,
                "type": ftype,
                "location": item.get("location", ""),
                "weather_entity": item.get("weather_entity") or "",
                "forecast_type": item.get("forecast_type") or "daily",
                "forecast_days": int(item.get("forecast_days") or 4),
                "feels_like_entity": item.get("feels_like_entity") or "",
                "aqi_entity": item.get("aqi_entity") or "",
                "sensors": item.get("sensors") or [],
                "entities": item.get("entities") or [],
            })
        return feeds

    def validate(self) -> list[str]:
        problems = []
        if not self.ha_url:
            problems.append("HA_URL is not set (standalone mode)")
        if not self.ha_token:
            problems.append("No token available "
                            "(SUPERVISOR_TOKEN or HA_TOKEN)")
        if not self.feeds:
            problems.append("No feeds configured")
        return problems
