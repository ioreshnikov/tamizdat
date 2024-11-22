import logging
import string
from telegram.ext.updater import Updater

from validate_email import validate_email

from .models import User
from .response import (
    NoResponse,
    UserNotFoundResponse,
    UserAuthorizedResponse,
    NewUserAdminNotification,
    BookNotFoundResponse,
    EmailSentResponse,
    EmailFailedResponse,
    SearchResponse,
    BookInfoResponse,
    DownloadResponse,
    SettingsResponse,
    SettingsEmailChooseResponse,
    SettingsEmailSetResponse,
    SettingsEmailInvalidResponse)
from .system import stop_bot


class Command:
    def prepare(self, bot, message):
        pass

    def execute(self, bot, message, *args):
        raise NotImplementedError()

    def handle(self, bot, message, *args):
        response = self.prepare(bot, message)
        if response:
            return response
        return self.execute(bot, message, *args)

    def handle_message(self, update, context):
        message = update.message
        response = self.handle(context.bot, message, message.text)
        return response.serve(context.bot, message)

    def handle_command(self, update, context):
        message = update.message
        response = self.handle(context.bot, message, *context.args)
        return response.serve(context.bot, message)

    def handle_callback(self, update, context):
        message = update.callback_query.message
        response = self.handle(context.bot, message, *context.args)
        return response.serve(context.bot, message)

    def handle_command_regex(self, update, context):
        message = update.message
        response = self.handle(context.bot, message, *context.match.groups())
        return response.serve(context.bot, message)

    def handle_callback_regex(self, update, context):
        message = update.callback_query.message
        response = self.handle(context.bot, message, *context.match.groups())
        return response.serve(context.bot, message)


class UserCommand(Command):
    def get_user(self, user_id):
        return User.get_or_none(User.user_id == user_id)

    def prepare(self, bot, message):
        user = self.get_user(user_id=message.chat.id)

        if not user:
            user = User(
                user_id=message.chat.id,
                first_name=message.chat.first_name,
                last_name=message.chat.last_name,
                username=message.chat.username)
            user.save()
            return NewUserAdminNotification(user)

        if not user.is_authorized:
            return NoResponse()

        self.user = user


class AdminCommand(UserCommand):
    def prepare(self, bot, message):
        user = self.get_user(user_id=message.chat.id)
        if not user or not user.is_admin:
            logging.error(
                "Admin command {} from user {} not executed"
                .format(message.text, message.chat.id))
            return NoResponse()

        self.user = user


class AuthorizeUserCommand(AdminCommand):
    def execute(self, bot, message, user_id):
        user = self.get_user(user_id)
        if not user:
            return UserNotFoundResponse()

        user.is_authorized = True
        user.save()

        return UserAuthorizedResponse()


class SettingsCommand(UserCommand):
    def execute(self, bot, message):
        return SettingsResponse(self.user)


class SettingsEmailChooseCommand(UserCommand):
    def execute(self, bot, message):
        self.user.next_message_is_email = True
        self.user.save()

        return SettingsEmailChooseResponse()


class SettingsEmailSetCommand(UserCommand):
    def execute(self, bot, message, email):
        if not validate_email(email):
            return SettingsEmailInvalidResponse()

        self.user.email = email
        self.user.next_message_is_email = False
        self.user.save()

        return SettingsEmailSetResponse(self.user.email)


class SearchCommand(UserCommand):
    def __init__(self, index):
        self.index = index
        self.translator = str.maketrans(dict.fromkeys(string.punctuation))

    def execute(self, bot, message, search_term):
        search_term = search_term.translate(self.translator)
        books = self.index.search(search_term)
        if not books:
            return BookNotFoundResponse()
        return SearchResponse(books)


class MessageCommand(UserCommand):
    def __init__(self, index):
        self.search_command = SearchCommand(index)
        self.settings_email_set_command = SettingsEmailSetCommand()

    def execute(self, bot, message, text):
        if self.user.next_message_is_email:
            return self.settings_email_set_command.handle(bot, message, text)
        else:
            return self.search_command.handle(bot, message, text)


class BookInfoCommand(UserCommand):
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        book = self.index.get(book_id)
        if not book:
            return BookNotFoundResponse()
        self.website.fetch_additional_info(book)
        return BookInfoResponse(book)


class DownloadCommand(UserCommand):
    def __init__(self, index, website):
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        book = self.index.get(book_id)
        if not book:
            return BookNotFoundResponse()

        logging.info("Asked for ebook for book_id={}".format(book_id))
        try:
            self.website.download_file(book.ebook_epub)
            if book.cover_image:
                self.website.download_file(book.cover_image)
        except Exception as error:
            logging.error(
                "Failed to download file: {}".format(error), exc_info=True)
            return EmailFailedResponse(self.user)
        else:
            return DownloadResponse(book)


class EmailCommand(UserCommand):
    def __init__(self, index, website, mailer):
        self.index = index
        self.website = website
        self.mailer = mailer

    def execute(self, bot, message, book_id):
        download = DownloadCommand(self.index, self.website)
        response = download.handle(bot, message, book_id)
        if isinstance(response, BookNotFoundResponse):
            return response

        if self.user.email is None:
            return SettingsEmailChooseCommand().handle(bot, message)

        book = self.index.get(book_id)
        try:
            self.mailer.send(book, self.user)
        except Exception as error:
            logging.error(
                "Failed sending email: {}".format(error), exc_info=True)
            return EmailFailedResponse(self.user)
        else:
            return EmailSentResponse(self.user)


class RestartCommand(AdminCommand):
    def __init__(self, updater: Updater):
        self.updater = updater

    def execute(self, *_):
        logging.info("Received restart command. Exiting")
        stop_bot(self.updater)
