ARG BUILD_FROM
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

# The HA base image provides the s6 init; run.sh is our service entrypoint.
CMD ["/run.sh"]
