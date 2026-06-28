#!/usr/bin/with-contenv bashio
# Entry point for the TRMNL HA Bridge add-on.
#
# Configuration is read by bridge.py directly from /data/options.json (written
# by the Supervisor from the UI), and HA is reached via the Supervisor proxy
# using $SUPERVISOR_TOKEN. There is nothing to template here — just launch.

bashio::log.info "Starting TRMNL HA Bridge..."
bashio::log.info "Feeds configured: $(bashio::config 'feeds | length')"

# Surface a clear error if the user removed all feeds.
if [ "$(bashio::config 'feeds | length')" -eq 0 ]; then
  bashio::log.warning "No feeds configured — add at least one in the add-on Configuration tab."
fi

exec python3 /app/bridge.py
