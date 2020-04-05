FROM ubuntu:18.04

COPY . /home
RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-setuptools && \
      pip3 install -r /home/requirements.txt && \
      chmod 755 /home/kook-tracker/entrypoint.sh

EXPOSE 5000
WORKDIR /home/kook-tracker
RUN ls -l
ENTRYPOINT ./entrypoint.sh