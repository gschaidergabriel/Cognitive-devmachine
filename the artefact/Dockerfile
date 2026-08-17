FROM python:3.13.14-slim-trixie@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ARG CLAUDE_CODE_SPEC=@anthropic-ai/claude-code@2.1.220
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLAYVERSE_STATE_ROOT=/var/lib/clayverse \
    CLAYVERSE_WORKSPACE=/workspace \
    CLAYVERSE_REQUIRE_CLAUDE=1 \
    CLAYVERSE_REQUIRE_ENTITYOS=0 \
    PORT=3000 \
    DISABLE_AUTOUPDATER=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates nodejs npm \
 && npm install --global "${CLAUDE_CODE_SPEC}" \
 && npm cache clean --force \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/clayverse
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY clayverse ./clayverse
RUN useradd --system --uid 10001 --create-home clayverse \
 && mkdir -p /var/lib/clayverse /workspace /home/clayverse/.claude /opt/entityos \
 && chown -R clayverse:clayverse /opt/clayverse /var/lib/clayverse /workspace /home/clayverse/.claude \
 && chown root:root /opt/entityos \
 && chmod 0755 /opt/entityos

USER clayverse
VOLUME ["/var/lib/clayverse"]
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python","-c","import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','3000')+'/healthz',timeout=3).read()"]
ENTRYPOINT ["python","-m","clayverse.service"]
