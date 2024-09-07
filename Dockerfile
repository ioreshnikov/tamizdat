FROM python:3.10-alpine

RUN apk add --no-cache sqlite

WORKDIR /tamizdat
COPY . .

RUN cd /tamizdat && python3 -m pip install .

CMD tamizdat bot
