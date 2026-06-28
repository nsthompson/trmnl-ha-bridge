"""TRMNL HA Bridge — Home Assistant -> TRMNL/Terminus JSON bridge.

Polls a local Home Assistant instance and exposes one display-ready JSON
document per configured *feed*, for Terminus "Poll" extensions to consume as
`source_1`. Each feed is its own endpoint (`/feeds/<slug>.json`), so a single
bridge can drive any number of screens / sensor combinations.

Two run modes, auto-detected:

  * Add-on mode  — when `/data/options.json` exists (the Home Assistant
    Supervisor writes the UI configuration there). HA is reached through the
    Supervisor proxy at http://supervisor/core/api using $SUPERVISOR_TOKEN, so
    no long-lived token and no file editing are required.

  * Standalone mode — configuration from environment variables + an optional
    JSON config file. HA is reached at $HA_URL with $HA_TOKEN. Useful when not
    running under the Supervisor (e.g. plain Docker / HA Container).

The feed-serving core is stdlib-only; PyYAML is used only to read the optional
``templates.yaml`` panel metadata (imported lazily).

Package layout:

  * Core (HA access + payload assembly): ``settings``, ``ha``, ``formatting``,
    ``weather``, ``sensors``, ``aqi``, ``templates``, ``payload``.
  * Web/UI: ``feedserver`` (the JSON feed server) and ``panel`` (the Ingress
    config UI; its HTML/CSS/JS live in ``panel_assets/``).
  * Entry point / wiring: ``cli`` (CLI flags + ``serve()``).
"""

__version__ = "1.1.0"
