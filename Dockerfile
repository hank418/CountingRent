FROM debian:stable
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install line-bot-sdk flask
RUN mkdir /vol
COPY lineApi.py /vol/
COPY sqlite.py /vol/
COPY secure.key /vol/
EXPOSE 8080
VOLUME ["/vol/rent.db"]
COPY startup.sh /
CMD ["sh", "/startup.sh"]
