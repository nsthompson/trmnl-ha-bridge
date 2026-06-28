# Adding the HA Weather extension to Terminus

This walks through creating the **Poll** extension in Terminus (`byos_hanami`)
that consumes a **TRMNL HA Bridge** feed and renders it to your TRMNL OG.

> Prerequisite: the **TRMNL HA Bridge** add-on (see [`../addon/`](../addon)) is
> installed, configured with at least one feed, and started. Each feed has a
> `slug` and is served at `http://<HA-host>:8080/feeds/<slug>.json`. Confirm with:
> ```
> curl http://<HA-host>:8080/feeds/main.json
> ```
> You should get the JSON document (see [`sample-output.json`](sample-output.json)).
> Create one Terminus extension per feed you want on a display.

## 1. Create the extension

1. In Terminus, open **Extensions** and click the **＋** (plus) icon.
2. Fill in:
   - **Label**: `HA Weather`
   - **Name**: `ha_weather`
   - **Kind**: `Poll`
3. Under **Build Matrix**, select your device model (TRMNL OG → 800×480, 1-bit).

## 2. Add the data exchange (the poll URL)

1. Add an **Exchange** with the feed URL from the add-on:
   ```
   http://<HA-host-ip>:8080/feeds/<slug>.json
   ```
   Use the HA host's LAN IP that Terminus can reach — not `localhost`, unless
   Terminus runs on the very same host. `<slug>` is the feed's slug (e.g. `main`).
2. Verb: **GET**. No headers needed (the add-on talks to HA itself).

The parsed JSON is exposed to your template as **`source_1`** (the first
exchange). The field shape is documented in
[`sample-output.json`](sample-output.json).

## 3. Paste the template

Open the template editor. It already provides a
`<div class="layout layout--col">` wrapper. Open
[`views/full.liquid`](views/full.liquid) and copy everything **between** the
`<!-- BEGIN extension content -->` and `<!-- END extension content -->`
markers, then paste it into the editor.

> The `BEGIN/END` region now **includes the title bar** (pinned to the bottom
> with `margin-top:auto`), so copying between the markers gives you the footer
> too. Only the outer `screen`/`view`/`layout` wrappers sit outside the markers —
> Terminus supplies those. Paste exactly what's between the markers.

If you also use half/quadrant slots in a mashup, repeat with the matching file
in [`views/`](views).

## 4. Preview, schedule, build

1. Use the **Preview** to confirm it renders at 800×480 in 1-bit.
2. Set a **Schedule** to rebuild on an interval (e.g. every 15 min). Keep this
   ≥ the add-on's `cache_ttl` so you're not rebuilding faster than data changes.
3. **Save**. The rendered screen now appears in the **Screens** UI.

## 5. Add to a playlist

Add the new screen to the **playlist** assigned to your TRMNL OG. On its next
wake/refresh the device will pull it. Set the device **Refresh Rate** to taste
(e.g. 900–1800 s) — slower is easier on the battery.

## Tuning the layout

- **Which sensors show** is controlled entirely by the add-on's feed config in
  the HA UI (`sensors` and `entities` lists) — no template edits needed to
  add/remove a reading.
- The templates use only core framework classes (`value`, `value--tnums`,
  `label`, `columns`/`column`, `grid`, `item`, `content`). Browse the framework
  docs at <https://trmnl.com/framework> for spacing/alignment utilities if you
  want to fine-tune.
- For crisp 1-bit numbers, the value spans use `value--tnums` (tabular figures)
  so digits don't jump between refreshes.
