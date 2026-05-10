FROM python:3.12-slim-bookworm
ENV DEBIAN_FRONTEND="noninteractive"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN set -ex \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            libpq-dev \
            gcc \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install deps in their own layer for better caching
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project --no-dev

COPY kook-tracker /app/kook-tracker
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/kook-tracker
EXPOSE 5000

ENTRYPOINT flask db upgrade && flask run
