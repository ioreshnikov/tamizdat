import logging

from validate_email import validate_email

from .models import User
from .response import (
    NotFoundResponse,
    EmailSentResponse,
    EmailFailedResponse,
    SearchResponse,
    BookInfoResponse,
    DownloadResponse,
    ProfileResponse,
    ProfileExtensionChooseResponse,
    ProfileExtensionSetResponse,
    ProfileEmailChooseResponse,
    ProfileEmailSetResponse,
    ProfileEmailInvalidResponse)


def get_or_create_user(chat):
    user, _ = User.get_or_create(user_id=chat.id)

    for attr in ("username", "first_name", "last_name"):
        stored_attr = getattr(user, attr)
        update_attr = getattr(chat, attr)
        if stored_attr != update_attr:
            setattr(user, attr, update_attr)

    return user


class Command:
    def execute(self, bot, message, *args):
        raise NotImplementedError()

    def handle_message(self, bot, update):
        message = update.message
        response = self.execute(bot, message, message.text)
        return response.serve(bot, message)

    def handle_command(self, bot, update, args):
        message = update.message
        response = self.execute(bot, message, *args)
        return response.serve(bot, message)

    def handle_callback(self, bot, update, args):
        message = update.callback_query.message
        response = self.execute(bot, message, *args)
        return response.serve(bot, message)

    def handle_command_regex(self, bot, update, groups):
        message = update.message
        response = self.execute(bot, message, *groups)
        return response.serve(bot, message)

    def handle_callback_regex(self, bot, update, groups):
        message = update.callback_query.message
        response = self.execute(bot, message, *groups)
        return response.serve(bot, message)


class ProfileCommand(Command):
    def execute(self, bot, message, key=None):
        user = get_or_create_user(message.chat)
        return ProfileResponse(user)


class ProfileEmailChooseCommand(Command):
    def execute(self, bot, message):
        user = get_or_create_user(message.chat)
        user.next_message_is_email = True
        user.save()

        return ProfileEmailChooseResponse()


class ProfileEmailSetCommand(Command):
    def execute(self, bot, message, email):
        if not validate_email(email):
            return ProfileEmailInvalidResponse()

        user = get_or_create_user(message.chat)
        user.email = email
        user.next_message_is_email = False
        user.save()

        return ProfileEmailSetResponse(email)


class ProfileExtensionCommand(Command):
    def execute(self, bot, message, extension):
        if not extension:
            return ProfileExtensionChooseResponse()

        user = get_or_create_user(message.chat)
        user.extension = extension
        user.next_message_is_email = False
        user.save()

        return ProfileExtensionSetResponse(extension)


class SearchCommand(Command):
    def __init__(self, index):
        self.index = index

    def execute(self, bot, message, search_term):
        books = self.index.search(search_term)
        if not books:
            return NotFoundResponse()
        return SearchResponse(books)


class MessageCommand(Command):
    def __init__(self, index):
        self.search_command = SearchCommand(index)
        self.profile_email_set_command = ProfileEmailSetCommand()

    def execute(self, bot, message, text):
        user = get_or_create_user(message.chat)
        if user.next_message_is_email:
            return self.profile_email_set_command.execute(bot, message, text)
        else:
            return self.search_command.execute(bot, message, text)


class BookInfoCommand(Command):
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        book = self.index.get(book_id)
        if not book:
            return NotFoundResponse()
        self.website.fetch_additional_info(book)
        return BookInfoResponse(book)


class DownloadCommand(Command):
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        book = self.index.get(book_id)
        if not book:
            return NotFoundResponse()
        logging.info("Asked for ebook for book_id={}".format(book_id))

        ebook = book.ebook_mobi
        self.website.download_file(ebook)

        return DownloadResponse(book)


class EmailCommand(Command):
    def __init__(self, index, website, mailer):
        self.index = index
        self.website = website
        self.mailer = mailer

    def execute(self, bot, message, book_id):
        download = DownloadCommand(self.index, self.website)
        response = download.execute(bot, message, book_id)
        if isinstance(response, NotFoundResponse):
            return response

        book = self.index.get(book_id)
        user = get_or_create_user(message.chat)
        try:
            self.mailer.send(book, user)
        except Exception:
            return EmailFailedResponse(user)
        else:
            return EmailSentResponse(user)
