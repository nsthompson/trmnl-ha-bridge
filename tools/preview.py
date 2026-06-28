#!/usr/bin/env python3
"""Render a TRMNL/Terminus Liquid view to a standalone HTML file.

Wraps the rendered markup with the real TRMNL framework CSS and the
`.screen--og` device class, then forces the screen to the view's true slot
size so headless Chrome rasterizes it the way Terminus would composite it.

Usage: preview.py <view.liquid> <out.html> <sample.json> <width> <height>
"""
import json
import os
import pathlib
import sys

from liquid import Environment

view, out_html, sample = sys.argv[1], sys.argv[2], sys.argv[3]
width, height = int(sys.argv[4]), int(sys.argv[5])
data = json.loads(pathlib.Path(sample).read_text())

body = Environment().from_string(pathlib.Path(view).read_text()).render(source_1=data)

# Apply the device + bit-depth modifiers to the template's own .screen div.
body = body.replace('<div class="screen">',
                    '<div class="screen screen--og screen--1bit">', 1)

# Force the screen + view to the slot's true dimensions (half/quadrant slots are
# smaller than the 800x480 device, and would otherwise stretch when previewed
# in isolation).
override = (
    f"html,body{{margin:0;padding:0;background:#fff;}}"
    f".screen{{width:{width}px!important;height:{height}px!important;"
    f"transform:none!important;margin:0!important;}}"
    f".view{{width:100%!important;height:100%!important;}}"
)

# MONO=1 approximates the device's 1-bit threshold (grayscale + hard contrast)
# so you can spot thin anti-aliased strokes that the e-ink would drop.
if os.environ.get("MONO", "").lower() in ("1", "true", "yes"):
    override += ".screen{filter:grayscale(1) contrast(10);}"

html = f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://trmnl.com/css/latest/plugins.min.css">
<style>{override}</style>
</head>
<body class="environment trmnl">
{body}
</body></html>"""
pathlib.Path(out_html).write_text(html)
print(f"  rendered {pathlib.Path(view).name} @ {width}x{height}")
