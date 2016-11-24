FROM alpine:latest
MAINTAINER lqf.1996121@gmail.com

# System dependencies
RUN apk update && apk add python3 python3-dev gcc libc-dev
# Python dependencies
RUN pip3 install flask==0.11.1 flask-sqlalchemy==2.1 marshmallow==2.10.4 gevent==1.1.2
# Remove build dependencies
RUN apk del python3-dev gcc libc-dev

EXPOSE 8080/tcp
CMD ["/root/project/app.py"]
