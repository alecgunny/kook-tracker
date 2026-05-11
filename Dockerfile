FROM python:3.12-slim-bookworm
ENV DEBIAN_FRONTEND="noninteractive"

RUN set -ex \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            libpq-dev \
            gcc \
        && rm -rf /var/lib/apt/lists/* \
        && pip install --no-cache-dir uv

WORKDIR /app

# install deps in their own layer for better caching
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project --no-dev

COPY kook-tracker /app/kook-tracker
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/kook-tracker

# Railway injects $PORT; shell-form CMD so it expands at runtime.
# --timeout 300: /event-results triggers a long serial WSL scrape; default 30s kills the worker.
CMD flask db upgrade && gunicorn --timeout 300 -b 0.0.0.0:${PORT:-5000} "app:app"
