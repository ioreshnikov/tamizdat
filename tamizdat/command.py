import logging
import os

from transliterate import translit

from .response import (
    NotFoundResponse,
    SearchResponse,
    BookInfoResponse,
    DownloadResponse)


class SearchCommand:
    def __init__(self, index):
        self.index = index

    def execute(self, term):
        books = self.index.search(term)
        if not books:
            return NotFoundResponse()
        return SearchResponse(books)

    def handle_message(self, bot, update):
        term = update.message.text
        response = self.execute(term)
        response.serve(bot, update)


class BookInfoCommand:
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, book_id):
        book = self.index.get(book_id)
        if not book:
            return NotFoundResponse()
        self.website.fetch_additional_info(book)
        return BookInfoResponse(book)

    def handle_regexp(self, bot, update, groups):
        book_id, *_ = groups
        response = self.execute(book_id)
        response.serve(bot, update)


class DownloadCommand:
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, book_id):
        book = self.index.get(book_id)
        if not book:
            return NotFoundResponse()
        logging.info("Asked for ebook for book_id={}".format(book_id))

        ebook = book.ebook_mobi
        self.website.download_file(ebook)

        return DownloadResponse(ebook)

    def handle_regexp(self, bot, update, groups):
        book_id, *_ = groups
        response = self.execute(book_id)
        response.serve(bot, update)
