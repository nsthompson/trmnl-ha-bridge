# TRMNL HA Bridge

Serve your Home Assistant **weather, forecast, AQI, and sensor data** as
TRMNL/Terminus-ready JSON **feeds** for an e-ink display — fully local, no cloud,
and no access token to create (the add-on talks to HA through the Supervisor).

![Logo](logo.png)

## What it does

- Polls Home Assistant and exposes one JSON **feed** per screen at
  `http://<HA-host>:8080/feeds/<slug>.json` for a Terminus "Poll" extension.
- Configure everything in the **config panel** (sidebar / *Open Web UI*): pick
  entities from type-ahead dropdowns — no typing entity IDs. Saving applies live.
- Two feed types: **Weather feed** (weather + forecast + AQI + sensors) or a
  generic **Sensor feed** (sensor/entity readings only).
- A **Templates** tab serves ready-to-paste Liquid layouts (full / half / quadrant)
  and is extensible — drop your own `.liquid` + `templates.yaml` into
  `/data/templates`.

## Install

1. **Settings → Add-ons → Add-on Store** → ⋮ → **Repositories** → add this repo's
   Git URL, then install **TRMNL HA Bridge** (or copy the `addon/` folder into
   your HA `/addons` share for a Local add-on).
2. **Start** it (enable *Start on boot* + *Watchdog*), open the config panel, add
   a feed, and **Save**.
3. In Terminus, create a **Poll** extension per feed, set its Exchange URL to the
   feed URL, and paste a template from the Templates tab.

See **DOCS.md** (the add-on's Documentation tab) for the full option reference,
feed types, endpoints, and troubleshooting.

## Endpoints

- `GET /` — list feeds and URLs · `GET /feeds/<slug>.json` — a feed payload ·
  `GET /health` — liveness.
