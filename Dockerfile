FROM ubuntu:18.04

COPY ./ /home/
WORKDIR /home

RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 \
        python3-pip && \
      pip3 install -f requirements.txt

EXPOSE 5000
ENTRYPOINT /home/entrypoint.sh
