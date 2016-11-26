FROM alpine:latest
MAINTAINER lqf.1996121@gmail.com

# System dependencies
RUN apk update && apk add python3 python3-dev gcc libc-dev
# Python dependencies
RUN pip3 install flask==0.11.1 flask-sqlalchemy==2.1 marshmallow==2.10.4 marshmallow-sqlalchemy==0.12.0 gevent==1.1.2 pg8000==1.10.6
# Remove build dependencies
RUN apk del python3-dev gcc libc-dev

# Expose port
EXPOSE 8080/tcp
# Working directory
WORKDIR /root/project
# Entry
CMD ["./server.py"]
