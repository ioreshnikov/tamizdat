import logging
import os

from .models import User
from .response import (
    NotFoundResponse,
    EmailSentResponse,
    EmailFailedResponse,
    GetEmailResponse,
    SetEmailResponse,
    GetFormatResponse,
    SetFormatResponse,
    SearchResponse,
    BookInfoResponse,
    DownloadResponse)


def get_or_create_user(chat):
    user, _ = User.get_or_create(user_id=chat.id)

    for attr in ("username", "first_name", "last_name"):
        stored_attr = getattr(user, attr)
        update_attr = getattr(chat, attr)
        if stored_attr != update_attr:
            setattr(user, attr, update_attr)

    return user


class SetEmailCommand:
    def get_email(self, bot, update, user):
        return GetEmailResponse(user).serve(bot, update)

    def set_email(self, bot, update, user, args):
        email, *_ = args
        logging.debug("Trying to set user email to {}".format(email))

        user.email = email
        user.save()

        logging.info("Updated user_id={} email to {}".format(
            user.user_id, user.email))

        return SetEmailResponse(user).serve(bot, update)

    def handle_command(self, bot, update, args):
        user = get_or_create_user(update.message.chat)
        if not args:
            self.get_email(bot, update, user)
        else:
            self.set_email(bot, update, user, args)


class SetFormatCommand:
    def get_format(self, bot, update, user):
        return GetFormatResponse(user).serve(bot, update)

    def set_format(self, bot, update, user, args):
        format_, *_ = args
        logging.debug("Trying to set user ebook format to {}".format(format_))

        user.format = format_
        user.save()

        logging.info("Updated user_id={} preferred format to {}".format(
            user.user_id, user.format))

        return SetFormatResponse(user).serve(bot, update)

    def handle_command(self, bot, update, args):
        user = get_or_create_user(update.message.chat)
        if not args:
            self.get_format(bot, update, user)
        else:
            self.set_format(bot, update, user, args)


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

        return DownloadResponse(book)

    def handle_regexp(self, bot, update, groups):
        book_id, *_ = groups
        response = self.execute(book_id)
        response.serve(bot, update)


class EmailCommand:
    def __init__(self, index, website, mailer):
        self.index = index
        self.website = website
        self.mailer = mailer

    def execute(self, book_id, user):
        response = DownloadCommand(self.index, self.website).execute(book_id)
        if isinstance(response, NotFoundResponse):
            return response
        book = self.index.get(book_id)
        try:
            self.mailer.send(book, user)
        except Exception:
            return EmailFailedResponse()
        else:
            return EmailSentResponse(user)

    def handle_regexp(self, bot, update, groups):
        book_id, *_ = groups
        user = get_or_create_user(update.callback_query.message.chat)
        response = self.execute(book_id, user=user)
        response.serve(bot, update)
