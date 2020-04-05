FROM ubuntu:18.04

COPY ./ /home/
RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 \
        python3-pip && \
      pip3 install -f /home/requirements.txt

EXPOSE 5000
WORKDIR /home/kook-tracker
ENTRYPOINT entrypoint.sh
