# https://developers.home-assistant.io/docs/apps/configuration#app-dockerfile
# Single multi-arch Home Assistant base image (Alpine + s6 + bashio). The CI
# builder overrides BUILD_FROM per build; the default lets it build standalone.
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23
FROM ${BUILD_FROM}

# Python runtime + PyYAML (reads the templates.yaml panel metadata) + tzdata so
# strftime weekday abbreviations resolve correctly. The feed-serving core itself
# is stdlib-only; PyYAML is used only for the optional template metadata.
RUN apk add --no-cache python3 py3-yaml tzdata

COPY bridge.py /app/bridge.py
COPY trmnl_bridge/ /app/trmnl_bridge/
COPY templates/ /app/templates/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

LABEL \
    org.opencontainers.image.title="TRMNL HA Bridge" \
    org.opencontainers.image.description="Serves Home Assistant weather, forecast and sensor data as TRMNL/Terminus JSON feeds for e-ink displays." \
    org.opencontainers.image.source="https://github.com/nsthompson/trmnl-ha-bridge" \
    org.opencontainers.image.licenses="MIT"

# The HA base image provides the s6 init; run.sh is our service entrypoint.
CMD ["/run.sh"]
