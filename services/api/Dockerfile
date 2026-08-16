FROM python:3.13.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system personalattice \
    && adduser --system --ingroup personalattice --home /app personalattice \
    && mkdir -p /var/data/personalattice \
    && chown -R personalattice:personalattice /app /var/data/personalattice

COPY services/api /app/services/api
RUN python -m pip install --no-cache-dir -e "/app/services/api"

USER personalattice

ENV PERSONALATTICE_DB_PATH=/var/data/personalattice/personalattice.db \
    PERSONALATTICE_CASE_RETENTION_DAYS=30 \
    PERSONALATTICE_COOKIE_SECURE=true

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --app-dir /app/services/api --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
