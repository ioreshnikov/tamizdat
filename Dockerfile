FROM python:3.10-alpine

RUN apk add --no-cache sqlite

WORKDIR /tamizdat
COPY . .

RUN cd /tamizdat && python3 -m pip install .
# RUN cd /tamizdat && tamizdat --database ./data/sqlite/index.sqlite3 --ebook_dir ./data/ebooks/ admin 237469848

CMD tamizdat --database ./data/sqlite/index.sqlite3 --ebook_dir ./data/ebooks/  bot
