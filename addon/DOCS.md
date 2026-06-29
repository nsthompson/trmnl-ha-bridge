# TRMNL HA Bridge

Serves your Home Assistant weather, forecast, and sensor data as
TRMNL/Terminus-ready JSON **feeds** that an e-ink display can poll. Everything is
configured in the add-on's **config panel** (entity dropdowns; **Open Web UI** /
sidebar) — no files to edit and no access token to create (the add-on talks to
HA through the Supervisor).

## How it works

```
Home Assistant ──(Supervisor proxy)──> TRMNL HA Bridge ──/feeds/<slug>.json──> Terminus (Poll) ──> TRMNL display
```

You define one or more **feeds**. Each feed:

- targets a `weather.*` entity (optional) for current conditions + forecast,
- lists any number of `sensor.*` (or other) entities to display,
- is published at its own URL: `http://<HA-host>:8080/feeds/<slug>.json`.

Point a separate Terminus "Poll" extension at each feed URL. That's how one
display (or several) can show any number of sensors or sensor combinations.

## Installation

1. **Settings → Add-ons → Add-on Store**.
2. Either install from the repository (⋮ → **Repositories** → add the Git URL,
   then pick **TRMNL HA Bridge**), or copy this `addon/` folder into your HA
   `/addons` share to install it as a **Local add-on**.
3. **Start** the add-on (enable **Start on boot** and **Watchdog**), then set up
   your feeds in the config panel (below).

## Configuration

### Feeds — in the config panel

Feeds are managed entirely in the **config panel**, not in the add-on options.
After starting the add-on, open it and click **Open Web UI** (it also appears in
the HA sidebar as *TRMNL Bridge*). The panel lists your Home Assistant entities
as **dropdowns** — pick the weather, feels-like, and AQI entities and add sensor
rows without typing entity IDs. **Save** applies immediately (no restart); the
feeds are stored in `/data/feeds.json`.

### Add-on options — the Configuration tab

The **Configuration** tab holds only runtime settings (feeds are no longer here):

| Option            | Meaning                                                       |
|-------------------|---------------------------------------------------------------|
| `cache_ttl`       | Seconds a feed is cached before re-querying HA (default 300). |
| `request_timeout` | Per-request timeout to HA, in seconds.                        |
| `log_level`       | Add-on log verbosity.                                         |

### Feed fields (reference)

Each **feed** you add in the panel has these fields (this is also the shape of
each entry in `/data/feeds.json`):

| Field            | Meaning                                                        |
|------------------|----------------------------------------------------------------|
| `type`           | `weather` (full weather + forecast + AQI + sensors) or `sensors` (generic — only sensor/entity readings; weather/forecast/AQI are skipped). In the panel, choose with **+ Weather feed** / **+ Sensor feed**. |
| `slug`           | URL-safe name → the feed is at `/feeds/<slug>.json`.          |
| `location`       | Title-bar label for the screen.                                |
| `weather_entity` | A `weather.*` entity (weather feeds only).                     |
| `forecast_type`  | `daily`, `hourly`, or `twice_daily`.                           |
| `forecast_days`  | How many forecast periods to include.                          |
| `feels_like_entity` | Optional sensor supplying the "feels like" temperature, for weather integrations (e.g. WeatherFlow Forecast) that don't expose `apparent_temperature`. Its state overrides `weather.apparent_temperature`. |
| `aqi_entity`     | Optional entity whose state is an AQI number (0–500). Adds an `air_quality` block with the AirNow category + level-of-concern face. |
| `sensors`        | List of `{entity_id, label}` — the primary sensor group.      |
| `entities`       | List of `{entity_id, label, unit}` — a second group.          |

`sensors` and `entities` are two named buckets with the same shape so a
template can lay them out separately. Add as many entries as fit your layout.

### Example feeds

Two feeds — one weather, one sensors-only — as you would set them up in the
panel (shown here as the structure stored in `/data/feeds.json`):

```yaml
- slug: living-room
  location: Living Room
  weather_entity: weather.forecast_home
  forecast_days: 4
  sensors:
    - entity_id: sensor.living_room_temperature
      label: Temp
    - entity_id: sensor.living_room_humidity
      label: Humidity
- slug: energy
  type: sensors
  location: Energy
  entities:
    - entity_id: sensor.solar_power
      label: Solar
      unit: W
    - entity_id: sensor.house_consumption
      label: Usage
      unit: W
```

→ served at `/feeds/living-room.json` and `/feeds/energy.json`.

## Connecting Terminus

Terminus has **no API to import templates or create extensions** (only a Screens
API for pushing pre-rendered HTML), so this is a quick manual step — and the
config panel gives you everything to copy:

1. In the panel, each feed shows its **Terminus Exchange URL**
   (`http://<HA-host>:8080/feeds/<slug>.json`) with a **Copy URL** button.
2. The **Terminus templates** section lists the full set of layouts (full,
   half_horizontal, half_vertical, quadrant) with **Copy template** buttons.
3. In Terminus: **Extensions → ＋ → Kind = Poll**, paste a template into the
   editor, add an **Exchange** with the feed URL, then **Build**. The parsed JSON
   is available to the template as `source_1`. One extension per feed.

## Endpoints

- `GET /` — lists configured feeds and their URLs.
- `GET /feeds/<slug>.json` — the display payload for a feed.
- `GET /health` — liveness check.
- `GET /trmnl.json` — alias for the first feed (back-compat convenience).

## Troubleshooting

- **Empty `forecast`** — confirm the `weather_entity` supports forecasts and
  that `forecast_type` matches one it provides. The add-on uses the current
  `weather.get_forecasts` service (the old inline `forecast` attribute was
  removed from HA ~2024.x).
- **A reading shows `—`** — that entity was `unavailable`/`unknown` or failed to
  fetch; the JSON `errors` array names the problem. One bad entity never blanks
  the rest of the feed.
- **Terminus can't reach the feed** — verify the port is published (it is by
  default) and use the HA host's LAN IP, not `localhost`. Check `GET /health`.
