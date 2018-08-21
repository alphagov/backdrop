FROM python:2.7.13-alpine
RUN apk --update add git alpine-sdk openssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm /var/cache/apk/*
COPY requirements.txt /
RUN pip install -r requirements.txt
ADD . /app
WORKDIR /app
ENTRYPOINT ["python", "start.py"]
