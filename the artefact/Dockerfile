FROM python:3.13-slim
WORKDIR /opt/clayverse
COPY clayverse.py /opt/clayverse/clayverse.py
RUN mkdir -p /var/lib/clayverse
VOLUME ["/var/lib/clayverse"]
ENTRYPOINT ["python3", "/opt/clayverse/clayverse.py"]
CMD ["--state", "/var/lib/clayverse"]
