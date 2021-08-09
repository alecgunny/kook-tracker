FROM python:3.8-slim-buster
ENV DEBIAN_FRONTEND="noninteractive"

# do environment set up
COPY requirements.txt /tmp/
RUN set -ex \
        \
        && apt-get update \
        \
        && apt-get install -y --no-install-recommends \
            postgresql \
            python-psycopg2 \
            libpq-dev \
            gcc \
        \
        && pip install wheel && pip install -r /tmp/requirements.txt \
        \
        && rm -rf /tmp/requirements.txt /var/lib/apt/lists/*

# set up the app specific settings
COPY kook-tracker /app
WORKDIR /app
EXPOSE 5000

ENTRYPOINT flask db upgrade && flask run
