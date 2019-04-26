import logging

from validate_email import validate_email

from .models import BOOK_EXTENSION_CHOICES, User
from .response import (
    NotFoundResponse,
    EmailSentResponse,
    EmailFailedResponse,
    SearchResponse,
    BookInfoResponse,
    DownloadResponse,
    SettingsResponse,
    SettingsExtensionChooseResponse,
    SettingsExtensionSetResponse,
    SettingsEmailChooseResponse,
    SettingsEmailSetResponse,
    SettingsEmailInvalidResponse)


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


class SettingsCommand(Command):
    def execute(self, bot, message, key=None):
        user = get_or_create_user(message.chat)
        return SettingsResponse(user)


class SettingsEmailChooseCommand(Command):
    def execute(self, bot, message):
        user = get_or_create_user(message.chat)
        user.next_message_is_email = True
        user.save()

        return SettingsEmailChooseResponse()


class SettingsEmailSetCommand(Command):
    def execute(self, bot, message, email):
        if not validate_email(email):
            return SettingsEmailInvalidResponse()

        user = get_or_create_user(message.chat)
        user.email = email
        user.next_message_is_email = False
        user.save()

        return SettingsEmailSetResponse(user)


class SettingsExtensionCommand(Command):
    def execute(self, bot, message, extension=None):
        if not extension or extension not in BOOK_EXTENSION_CHOICES:
            return SettingsExtensionChooseResponse()

        user = get_or_create_user(message.chat)
        user.extension = extension
        user.next_message_is_email = False
        user.save()

        return SettingsExtensionSetResponse(extension)


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
        self.settings_email_set_command = SettingsEmailSetCommand()

    def execute(self, bot, message, text):
        user = get_or_create_user(message.chat)
        if user.next_message_is_email:
            return self.settings_email_set_command.execute(bot, message, text)
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

        user = get_or_create_user(message.chat)
        if user.extension is None:
            return SettingsExtensionCommand().execute(bot, message)

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
        if not book:
            return NotFoundResponse()

        user = get_or_create_user(message.chat)
        if user.extension is None:
            return SettingsExtensionCommand().execute(bot, message)
        if user.email is None:
            return SettingsEmailChooseCommand().execute(bot, message)

        try:
            self.mailer.send(book, user)
        except Exception as error:
            logging.error(
                "Failed sending email: {}".format(error), exc_info=True)
            return EmailFailedResponse(user)
        else:
            return EmailSentResponse(user)
