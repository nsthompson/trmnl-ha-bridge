# Bundled Terminus templates

Paste-ready Liquid templates surfaced in the config panel's **Templates** tab.
The panel discovers templates **dynamically**: every `*.liquid` file here (and in
an optional `/data/templates` overlay) is listed, described by `templates.yaml`.

## `templates.yaml`

Ordered metadata, one entry per template file:

```yaml
templates:
  - file: full.liquid
    label: Full
    size: 800×480
    category: Weather
    description: What this template shows…
```

`label`, `size`, `category`, and `description` are shown on the card. Files with
no metadata entry still appear (label derived from the filename); entries whose
file is missing are skipped.

## Add your own (any use case, not just weather)

Drop a `<name>.liquid` (using whatever `source_1.*` fields your feed exposes) plus
a matching entry into **`/data/templates/`** and its **`/data/templates/templates.yaml`**
on the add-on host — no rebuild needed; it appears in the panel automatically.

## These bundled copies

The `*.liquid` files here are copies of `../../extension/views/*.liquid` — the
TRMNL OG layouts plus the TRMNL X (`-x`) greyscale variants. Keep them in sync
after edits (the `_weather-icons.liquid` reference partial is intentionally not
bundled):

    cp ../../extension/views/{full,half_horizontal,half_vertical,quadrant}{,-x}.liquid .
