# HA Weather — TRMNL OG + Home Assistant

Show **current weather, a multi-day forecast, indoor sensors, and any other
Home Assistant entities** on a TRMNL OG e-ink display (800×480, 1-bit) — fully
local, no cloud.

It has two parts:

1. **A Home Assistant add-on** (`addon/`) — *TRMNL HA Bridge*. Installed and
   configured entirely through the HA UI; no file editing and no access token to
   create. It exposes one JSON **feed** per screen you want.
2. **Terminus extension assets** (`extension/`) — ready-made Liquid templates +
   setup guide for a Terminus "Poll" extension that renders a feed.

## Architecture

```text
┌──────────────────┐  Supervisor   ┌─────────────────┐   one URL per feed   ┌────────────────────┐   BMP   ┌──────────┐
│  Home Assistant  │  proxy (no    │  TRMNL HA Bridge│  /feeds/<slug>.json  │ Terminus Extension │ ──────► │ TRMNL OG │
│  (local)         │  token!)  ──► │  (HA add-on)    │ ───────────────────► │ (Poll + Liquid)    │  render │  e-ink   │
└──────────────────┘               └─────────────────┘     = source_1       └────────────────────┘         └──────────┘
```

**Why a bridge add-on?** A Terminus "Poll" exchange is a single HTTP GET. Home
Assistant needs several calls — one `GET /api/states/<id>` per entity **plus** a
`POST weather.get_forecasts` service call — behind authentication. Running as an
add-on, the bridge reaches HA through the Supervisor proxy (so there's no token
to manage), does that orchestration, formats it (units, weekday labels,
human-readable conditions, unavailable-entity handling), and serves clean JSON.

**Why "feeds"?** Each feed is an independent endpoint with its own weather entity
and sensor lists. Add as many as you like in the UI; point one Terminus
extension at each. That's how one bridge drives any number of sensors or sensor
combinations across one or several displays.

## Layout

```text
trmnl-ha-bridge/
├── repository.yaml          # lets you add this as a HA add-on repository
├── README.md                # this file
├── addon/                   # the Home Assistant add-on (TRMNL HA Bridge)
│   ├── config.yaml          # manifest + UI options schema (feeds, sensors…)
│   ├── build.yaml           # HA base images per arch
│   ├── Dockerfile
│   ├── run.sh               # bashio entrypoint
│   ├── bridge.py            # the app (multi-feed; add-on or standalone)
│   ├── translations/en.yaml # nice UI labels
│   ├── templates/           # bundled Liquid templates + templates.yaml (panel)
│   ├── icon.png  logo.png   # add-on store icon + banner
│   ├── README.md  DOCS.md   # add-on store text + Documentation tab
│   └── CHANGELOG.md
├── extension/               # the Terminus extension assets
│   ├── views/               # Liquid templates per layout
│   │   ├── full.liquid              # 800×480 — weather + forecast + sensor grid
│   │   ├── half_horizontal.liquid   # 800×240
│   │   ├── half_vertical.liquid     # 400×480
│   │   ├── quadrant.liquid          # 400×240
│   │   └── _weather-icons.liquid    # canonical icon/face reference block
│   ├── settings.yml         # poll config (for trmnlp / private-plugin import)
│   ├── sample-output.json   # the JSON shape a feed serves (source_1)
│   └── SETUP.md             # step-by-step Terminus setup
└── tools/                   # preview.sh / preview.py / validate.py (local render)
```

## Quick start

### 1. Install the add-on

- **Repository install**: HA → **Settings → Add-ons → Add-on Store** → ⋮ →
  **Repositories** → add this project's Git URL → install **TRMNL HA Bridge**.
- **Local install**: copy the [`addon/`](addon) folder into your HA `/addons`
  share; it appears under **Local add-ons**.

### 2. Configure feeds in the UI

Start the add-on (enable **Start on boot** + **Watchdog**), then open its
**config panel** (the add-on's *Open Web UI*, also in the HA sidebar as *TRMNL
Bridge*). Add **feeds** and pick the weather / feels-like / AQI entities and
sensor rows from **dropdowns of your HA entities** — no typing entity IDs.
**Save** applies live. (You can also edit feeds as YAML in the **Configuration**
tab.) See [`addon/DOCS.md`](addon/DOCS.md) for every option.

Verify a feed:

```bash
curl http://<HA-host>:8080/feeds/<slug>.json
curl http://<HA-host>:8080/            # lists all feeds and their URLs
```

### 3. Render it in Terminus

Follow [`extension/SETUP.md`](extension/SETUP.md): create a **Poll** extension
per feed, point its exchange at `http://<HA-host>:8080/feeds/<slug>.json`, paste
[`extension/views/full.liquid`](extension/views/full.liquid), preview, and add
the screen to your device's playlist.

## Running standalone (without the Supervisor)

The same `addon/bridge.py` runs outside HA (e.g. plain Docker / HA Container).
It auto-detects the mode: if `$SUPERVISOR_TOKEN` is absent it uses `$HA_URL` +
`$HA_TOKEN`, and reads feeds from `$CONFIG_PATH` (a JSON file with a `feeds`
list, same shape as the add-on options). CLI helpers:

```bash
HA_URL=http://homeassistant.local:8123 HA_TOKEN=... CONFIG_PATH=feeds.json \
  python3 addon/bridge.py --check   # verify connectivity + list feeds
  #                        --once    # print every feed's JSON and exit
  #                        (no flag)  # serve on $PORT (default 8080)
```

## Previewing templates locally

Before pushing a template to Terminus, rasterize it to a PNG with the real
TRMNL framework CSS so you can eyeball it — from the bundled sample, a local
JSON file, or **live data polled from the running bridge**:

```bash
tools/preview.sh                  # render every view from the bundled sample
tools/preview.sh full             # just one
SAMPLE=my-feed.json tools/preview.sh full          # a custom local JSON file

# Live data from the add-on (validates the payload, then renders it):
BRIDGE=http://homeassistant.local:8080 tools/preview.sh full
BRIDGE=http://10.0.0.5:8080 FEED=energy tools/preview.sh full   # pick a feed
FEED_URL=http://10.0.0.5:8080/feeds/main.json tools/preview.sh  # full URL

tools/preview.sh --validate       # validate only (live or sample), no render
MONO=1 tools/preview.sh full      # simulate the 1-bit e-ink threshold
```

`MONO=1` applies a grayscale + hard-contrast filter that approximates the
device's 1-bit conversion — useful for catching thin strokes (e.g. icon detail)
that render fine in color but would drop out on the e-ink panel.

Every run first **validates** the payload and prints a report — data freshness,
weather/forecast presence, AQI range, unavailable entities, and any errors the
bridge itself reported — so you catch a misconfigured entity or a stale feed
before it reaches the device. `--validate` exits non-zero on a hard failure
(useful for CI). PNGs land in `tools/preview-output/<view>.png`, each at its true
TRMNL OG slot size (full 800×480, half_horizontal 800×240, half_vertical
400×480, quadrant 400×240).

Requires `python3`, `curl`, Google Chrome/Chromium, and network access (the
framework CSS + fonts load from trmnl.com); a local venv with `python-liquid`
is created under `tools/.preview-venv` on first run.

## Notes & gotchas

- **Forecast API**: HA removed the inline `forecast` weather attribute (~2024.x).
  The bridge uses `POST /api/services/weather/get_forecasts?return_response`. If
  a forecast is empty, confirm the entity supports the chosen `forecast_type`.
- **1-bit design**: pure black/white only. Numeric readouts use `value--tnums`
  so digits stay aligned across refreshes.
- **Feels-like**: if your weather integration doesn't expose an apparent
  temperature (e.g. WeatherFlow Forecast), set a feed's `feels_like_entity` to a
  sensor that does — it fills `weather.apparent_temperature` so the "Feels like"
  reading appears.
- **Air Quality**: set a feed's `aqi_entity` (any entity whose state is an AQI
  number, 0–500) to get an `air_quality` block — the AirNow category (Good →
  Hazardous) plus a level-of-concern **face** (smile → distress) the templates
  render from the value. Omit it and the AQI section simply doesn't appear.
- **Feed types**: add a **Weather feed** (weather + forecast + AQI + sensors) or
  a generic **Sensor feed** (sensor/entity readings only) from the panel.
- **Refresh cadence**: keep the device refresh rate and the extension rebuild
  schedule ≥ the add-on `cache_ttl` (default 300s).
- **Resilience**: an `unavailable` entity or failed call is reported in the JSON
  `errors` array and shown as `—`; one bad entity never blanks a feed.

## Verified

- `addon/bridge.py` compiles and passes mocked tests covering: add-on mode +
  Supervisor-proxy URL, multi-feed serving, slug generation/dedup, sensors-only
  feeds, numeric coercion, forecast mapping, unavailable-entity handling, and
  the full HTTP route surface (`/`, `/feeds/<slug>.json`, `/health`, aliases,
  404s).
- The add-on manifest parses and its options schema matches HA's nested
  list-of-dicts format.
- The Liquid templates use only TRMNL framework classes confirmed against
  <https://trmnl.com/framework> (v3.1).
