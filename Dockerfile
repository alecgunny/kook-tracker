FROM ubuntu:18.04

COPY requirements.txt /tmp/
RUN set -ex \
        \
        && apt-get update \
        \
        && apt-get install -y --no-install-recommends \
            python3-dev \
            python3-pip \
            python3-setuptools \
            postgresql \
            python-psycopg2 \
            libpq-dev \
            gcc \
        \
        && pip3 install wheel && pip3 install -r /tmp/requirements.txt \
        \
        && rm -rf /tmp/requirements.txt /var/lib/apt/lists/*

COPY kook-tracker /app
WORKDIR /app
EXPOSE 5000

ENTRYPOINT flask db upgrade && flask run
