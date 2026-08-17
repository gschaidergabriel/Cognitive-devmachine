FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CLAYVERSE_STATE_ROOT=/var/lib/clayverse
RUN useradd --system --uid 10001 --create-home clayverse && mkdir -p /opt/clayverse /var/lib/clayverse && chown -R clayverse:clayverse /opt/clayverse /var/lib/clayverse
WORKDIR /opt/clayverse
COPY clayverse ./clayverse
USER clayverse
VOLUME ["/var/lib/clayverse"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD ["python","-m","clayverse.service","--once"]
ENTRYPOINT ["python","-m","clayverse.service"]
