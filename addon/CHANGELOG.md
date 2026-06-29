# Changelog

## 1.1.1

- **Remove `feeds` from the add-on options/schema.** Feeds have been managed in
  the config panel (stored in `/data/feeds.json`) since 1.1.0; the deprecated
  `feeds` option in the **Configuration** tab is now gone. Your existing feeds
  are unaffected — they live in `/data/feeds.json`. The Configuration tab now
  holds only `cache_ttl`, `request_timeout` and `log_level`. (If the Supervisor
  flags a leftover `feeds` key in your saved options after updating, clear it
  from the Configuration tab.)

## 1.1.0

- **Feed types:** add a feed as a **Weather feed** (weather entity, feels-like,
  AQI, forecast, sensors) or a generic **Sensor feed** (just sensor/entity
  readings — no weather/forecast/AQI prompts). The bridge skips weather-building
  for sensor feeds and tags the payload with `type`.

- **Config panel (Ingress):** a sidebar web UI to configure feeds by typing-to-
  search Home Assistant entities (autocomplete; the friendly name shows under
  each field). HA-styled with light/dark mode. Saving applies live (feeds stored
  in `/data/feeds.json`; no restart needed).
- **Collapsible feed cards:** each feed is a card that collapses to a one-line
  summary and expands to the full editor.
- **Templates tab:** a dedicated tab lists paste-ready Liquid templates as cards
  with size/category badges and descriptions, plus copy buttons and each feed's
  Terminus Exchange URL. (Terminus has no API to import templates/extensions —
  only a Screens API for pushing pre-rendered HTML — so the panel makes the
  templates available instead.)
- **Extensible templates:** templates are discovered dynamically from the
  template folders and described by a `templates.yaml` metadata file. Drop your
  own `<name>.liquid` + a metadata entry into `/data/templates` and it appears in
  the panel automatically — not limited to weather use cases.
- Bridge branding: add-on `icon.png` (a suspension bridge, replacing the default
  puzzle piece), `logo.png` banner for the add-on page, and sidebar panel icon
  (`mdi:bridge`).
- **Feels-like sensor:** new per-feed `feels_like_entity` supplies the apparent
  ("feels like") temperature for weather integrations that don't expose it
  (e.g. WeatherFlow Forecast); its state overrides `weather.apparent_temperature`.
- An empty feed list no longer blocks startup — add feeds in the panel.

## 1.0.0

- Initial release.
- Multi-feed support: define any number of feeds in the UI, each served at
  `/feeds/<slug>.json` for a separate Terminus Poll extension.
- Runs as a Home Assistant add-on using the Supervisor proxy (no long-lived
  token required); also runs standalone via `HA_URL`/`HA_TOKEN`.
- Current weather, multi-day forecast (`weather.get_forecasts`), and arbitrary
  sensor/entity groups, all configured from the Configuration tab.
