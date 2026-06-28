#!/usr/bin/env bash
#
# preview.sh — rasterize an HA Weather Liquid view to an 800x480 PNG using the
# real TRMNL framework CSS + headless Google Chrome, so you can eyeball a
# template before pushing it to Terminus / the device. Can render the static
# sample, a local JSON file, or LIVE data polled from the running bridge.
#
# Usage:
#   tools/preview.sh                         # all views, from the bundled sample
#   tools/preview.sh full                    # just full.liquid
#   tools/preview.sh full half_vertical      # a specific set
#   SAMPLE=path/to/data.json tools/preview.sh full          # custom local data
#
#   # LIVE data from the bridge (validates the payload, then renders it):
#   BRIDGE=http://homeassistant.local:8080 tools/preview.sh full
#   BRIDGE=http://10.0.0.5:8080 FEED=energy tools/preview.sh full   # pick a feed
#   FEED_URL=http://10.0.0.5:8080/feeds/main.json tools/preview.sh  # full URL
#
#   tools/preview.sh --validate              # validate only (live or sample), no render
#
# Output: tools/preview-output/<view>.png  (+ live.json when polling)
#
# Requirements: bash, python3, curl, Google Chrome, and network access (the
# framework CSS + fonts load from trmnl.com). A local venv with python-liquid is
# created on first run under tools/.preview-venv.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
views_dir="$root/extension/views"
out_dir="$here/preview-output"
venv="$here/.preview-venv"
mkdir -p "$out_dir"

# --- parse args: flags + explicit view names ----------------------------------
validate_only=0
views=()
for a in "$@"; do
  case "$a" in
    --validate|--validate-only) validate_only=1 ;;
    *) views+=("$a") ;;
  esac
done

# --- resolve the data source: live bridge feed, custom file, or sample --------
feed_name="${FEED:-main}"
if [ -n "${FEED_URL:-}" ]; then
  feed_url="$FEED_URL"
elif [ -n "${BRIDGE:-}" ]; then
  feed_url="${BRIDGE%/}/feeds/${feed_name}.json"
else
  feed_url=""
fi

if [ -n "$feed_url" ]; then
  sample="$out_dir/live.json"
  echo "polling live bridge: $feed_url"
  if ! curl -fsS -m 15 "$feed_url" -o "$sample"; then
    echo "error: could not reach the bridge at $feed_url" >&2
    echo "       check the URL/host, that the add-on is running, and the feed slug." >&2
    exit 1
  fi
  data_label="live ($feed_url)"
else
  sample="${SAMPLE:-$root/extension/sample-output.json}"
  feed_name="$(basename "$sample" .json)"
  data_label="$sample"
fi

# --- validate the payload (stdlib-only; runs for live or static) --------------
echo "data: $data_label"
validate_rc=0
python3 "$here/validate.py" "$sample" "$feed_name" || validate_rc=$?
if [ "$validate_only" -eq 1 ]; then
  exit "$validate_rc"
fi
if [ "$validate_rc" -ge 2 ]; then
  echo "error: payload is malformed; not rendering." >&2
  exit "$validate_rc"
fi
echo

# --- locate Google Chrome -----------------------------------------------------
chrome=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v google-chrome-stable 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)" \
  "$(command -v chromium-browser 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then chrome="$c"; break; fi
done
if [ -z "$chrome" ]; then
  echo "error: Google Chrome / Chromium not found." >&2
  exit 1
fi

# --- python env with python-liquid -------------------------------------------
if [ ! -x "$venv/bin/python" ]; then
  echo "setting up preview venv (one-time)..."
  python3 -m venv "$venv"
  "$venv/bin/pip" install --quiet --upgrade pip
  "$venv/bin/pip" install --quiet python-liquid
fi

# --- which views to render ----------------------------------------------------
if [ "${#views[@]}" -gt 0 ]; then
  names=("${views[@]}")
else
  names=()
  for f in "$views_dir"/*.liquid; do
    b="$(basename "$f" .liquid)"
    [ "${b:0:1}" = "_" ] && continue   # skip partials like _weather-icons
    names+=("$b")
  done
fi

# --- each view's true slot size on the TRMNL OG -------------------------------
slot_size() {
  case "$1" in
    full)            echo "800 480" ;;
    half_horizontal) echo "800 240" ;;
    half_vertical)   echo "400 480" ;;
    quadrant)        echo "400 240" ;;
    *)               echo "800 480" ;;   # sensible default
  esac
}

# --- render + screenshot each -------------------------------------------------
for name in "${names[@]}"; do
  view="$views_dir/$name.liquid"
  if [ ! -f "$view" ]; then echo "skip: no $view" >&2; continue; fi
  read -r w h <<<"$(slot_size "$name")"
  html="$out_dir/$name.html"
  png="$out_dir/$name.png"
  "$venv/bin/python" "$here/preview.py" "$view" "$html" "$sample" "$w" "$h"
  rm -f "$png"
  "$chrome" --headless --disable-gpu --hide-scrollbars --no-sandbox \
    --force-device-scale-factor=1 --window-size="$w,$h" \
    --default-background-color=FFFFFFFF --virtual-time-budget=12000 \
    --screenshot="$png" "$html" >/dev/null 2>&1 || true
  if [ -f "$png" ]; then echo "  -> $png ($w x $h)"; else echo "  !! failed: $name" >&2; fi
done

echo "done. PNGs in $out_dir"
