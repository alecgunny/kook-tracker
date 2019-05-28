FROM ubuntu:18.04
RUN apt-get update && \
      apt-get install python3 python3-pip && \
      pip install flask
COPY *.py /home
WORKDIR /home
EXPOSE 5000
CMD "FLASK_APP=app.py flask run"
