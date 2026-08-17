FROM python:3.13.14-slim-trixie@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ARG TARGETARCH
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

COPY SOURCE_LOCK.json /opt/clayverse-build/SOURCE_LOCK.json
COPY build/install_pinned_apt.py /opt/clayverse-build/install_pinned_apt.py

# Replace the mutable Debian mirror configuration inherited from the base image with
# the exact repository-owned snapshot contract before resolving any new OS package.
# APT still verifies Debian's signed Release -> Packages -> .deb hash chain; the
# fixed snapshot timestamp prevents later mirror state from changing the resolution.
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources \
 && python /opt/clayverse-build/install_pinned_apt.py --write-sources /etc/apt/sources.list.d/clayverse-snapshot.sources \
 && APT_PACKAGES="$(python /opt/clayverse-build/install_pinned_apt.py --print-packages)" \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${APT_PACKAGES} \
 && rm -rf /var/lib/apt/lists/*

# Browser xterm and native Claude Code are installed from repository-owned digest
# locks below rather than via npm.
COPY build/install_pinned_xterm.py /opt/clayverse-build/install_pinned_xterm.py
COPY build/install_pinned_claude.py /opt/clayverse-build/install_pinned_claude.py
RUN mkdir -p /opt/clayverse/vendor \
 && python /opt/clayverse-build/install_pinned_xterm.py \
 && test -f /opt/clayverse/vendor/xterm/lib/xterm.js \
 && test -f /opt/clayverse/vendor/xterm/css/xterm.css
RUN TARGETARCH="${TARGETARCH}" python /opt/clayverse-build/install_pinned_claude.py \
 && /usr/local/bin/claude --version

WORKDIR /opt/clayverse
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /etc/claude-code /opt/entityos /opt/clayverse/runtime
COPY --chown=root:root policy/managed-mcp.json /etc/claude-code/managed-mcp.json
COPY --chown=root:root policy/managed-settings.json /etc/claude-code/managed-settings.json
RUN chmod 0444 /etc/claude-code/managed-mcp.json /etc/claude-code/managed-settings.json
COPY clayverse ./clayverse
COPY --chown=root:root runtime_CLAUDE.md /opt/clayverse/runtime/CLAUDE.md
COPY --chown=root:root policy/deny-shell /opt/clayverse/runtime/deny-shell
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
 && chmod 0444 /opt/clayverse/runtime/CLAUDE.md \
 && chmod 0555 /opt/clayverse/runtime/deny-shell
RUN useradd --system --uid 10001 --create-home --shell /bin/bash clayverse \
 && mkdir -p /var/lib/clayverse /workspace /home/clayverse/.claude \
 && chown -R root:root /opt/clayverse \
 && chmod -R a-w /opt/clayverse \
 && chown -R clayverse:clayverse /var/lib/clayverse /workspace /home/clayverse/.claude \
 && chown root:root /opt/entityos /opt/entityos/EntityOS /opt/entityos/entityos.lock.json \
 && chmod 0755 /opt/entityos \
 && chmod 0555 /opt/entityos/EntityOS \
 && chmod 0444 /opt/entityos/entityos.lock.json

USER clayverse
VOLUME ["/var/lib/clayverse", "/workspace"]
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD ["python","-c","import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','3000')+'/readyz',timeout=3).read()"]
ENTRYPOINT ["python","-m","clayverse.service"]
