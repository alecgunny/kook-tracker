FROM ubuntu:18.04

COPY requirements.txt /tmp/
RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-setuptools && \
      pip3 install -r /tmp/requirements.txt && \
      rm /tmp/requirements.txt && \
      rm -rf /var/lib/apt/lists/*

COPY kook-tracker /app
WORKDIR /app
EXPOSE 5000
ENTRYPOINT /bin/bash -c "flask db init && flask db upgrade && flask run --host=0.0.0.0"
