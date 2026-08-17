FROM python:3.13.14-slim-trixie@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ARG CLAUDE_CODE_SPEC=@anthropic-ai/claude-code@2.1.220
ARG XTERM_SPEC=@xterm/xterm@6.0.0
ARG ENTITYOS_SHA256
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLAYVERSE_STATE_ROOT=/var/lib/clayverse \
    CLAYVERSE_WORKSPACE=/workspace \
    CLAYVERSE_REQUIRE_CLAUDE=1 \
    CLAYVERSE_ENABLE_ENTITYOS_EXEC=0 \
    CLAYVERSE_ENTITYOS_PATH=/opt/entityos/EntityOS \
    CLAYVERSE_ENTITYOS_SHA256=${ENTITYOS_SHA256} \
    PORT=3000 \
    DISABLE_AUTOUPDATER=1 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates nodejs npm tmux \
 && npm install --global "${CLAUDE_CODE_SPEC}" "${XTERM_SPEC}" \
 && mkdir -p /opt/clayverse/vendor \
 && cp -a "$(npm root -g)/@xterm/xterm" /opt/clayverse/vendor/xterm \
 && test -f /opt/clayverse/vendor/xterm/lib/xterm.js \
 && test -f /opt/clayverse/vendor/xterm/css/xterm.css \
 && npm cache clean --force \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/clayverse
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /etc/claude-code /opt/entityos /opt/clayverse/runtime
COPY --chown=root:root policy/managed-mcp.json /etc/claude-code/managed-mcp.json
RUN chmod 0444 /etc/claude-code/managed-mcp.json
COPY clayverse ./clayverse
COPY --chown=root:root runtime_CLAUDE.md /opt/clayverse/runtime/CLAUDE.md
COPY --chown=root:root entityos.lock.json /opt/entityos/entityos.lock.json
COPY --chown=root:root EntityOS /opt/entityos/EntityOS
RUN LOCK_SCHEMA="$(python -c 'import json; print(json.load(open("/opt/entityos/entityos.lock.json", encoding="utf-8"))["schema"])')" \
 && LOCK_SHA256="$(python -c 'import json; print(json.load(open("/opt/entityos/entityos.lock.json", encoding="utf-8"))["sha256"])')" \
 && LOCK_SIZE="$(python -c 'import json; print(json.load(open("/opt/entityos/entityos.lock.json", encoding="utf-8"))["size_bytes"])')" \
 && test "$LOCK_SCHEMA" = "ClayVerseEntityOSArtifactLock/v1" \
 && test -n "${ENTITYOS_SHA256}" \
 && test "${ENTITYOS_SHA256}" = "$LOCK_SHA256" \
 && test "$(stat -c %s /opt/entityos/EntityOS)" = "$LOCK_SIZE" \
 && printf '%s  %s\n' "$LOCK_SHA256" /opt/entityos/EntityOS | sha256sum -c - \
 && chmod 0555 /opt/entityos/EntityOS \
 && chmod 0444 /opt/entityos/entityos.lock.json \
 && chmod 0444 /opt/clayverse/runtime/CLAUDE.md
RUN useradd --system --uid 10001 --create-home --shell /bin/bash clayverse \
 && mkdir -p /var/lib/clayverse /workspace /home/clayverse/.claude \
 && chown -R clayverse:clayverse /opt/clayverse /var/lib/clayverse /workspace /home/clayverse/.claude \
 && chown root:root /opt/entityos /opt/entityos/EntityOS /opt/entityos/entityos.lock.json \
 && chmod 0755 /opt/entityos \
 && chmod 0555 /opt/entityos/EntityOS \
 && chmod 0444 /opt/entityos/entityos.lock.json

USER clayverse
VOLUME ["/var/lib/clayverse", "/workspace"]
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD ["python","-c","import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','3000')+'/healthz',timeout=3).read()"]
ENTRYPOINT ["python","-m","clayverse.service"]
