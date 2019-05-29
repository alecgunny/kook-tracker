FROM ubuntu:18.04
RUN apt-get update && \
      apt-get install -y --no-install-recommends python3 python3-pip && \
      pip3 install flask beautifulsoup4 lxml
COPY *.py /home/
WORKDIR /home
EXPOSE 5000
ENV FLASK_APP=/home/app.py LC_ALL=C.UTF-8 LANG=C.UTF-8

ENTRYPOINT ["flask", "run"]
CMD ["--host=0.0.0.0"]
