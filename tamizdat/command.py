import logging
from validate_email import validate_email

from .models import BOOK_EXTENSION_CHOICES, User
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
    SettingsExtensionChooseResponse,
    SettingsExtensionSetResponse,
    SettingsEmailChooseResponse,
    SettingsEmailSetResponse,
    SettingsEmailInvalidResponse)


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

    def handle_message(self, bot, update):
        message = update.message
        response = self.handle(bot, message, message.text)
        return response.serve(bot, message)

    def handle_command(self, bot, update, args):
        message = update.message
        response = self.handle(bot, message, *args)
        return response.serve(bot, message)

    def handle_callback(self, bot, update, args):
        message = update.callback_query.message
        response = self.handle(bot, message, *args)
        return response.serve(bot, message)

    def handle_command_regex(self, bot, update, groups):
        message = update.message
        response = self.handle(bot, message, *groups)
        return response.serve(bot, message)

    def handle_callback_regex(self, bot, update, groups):
        message = update.callback_query.message
        response = self.handle(bot, message, *groups)
        return response.serve(bot, message)


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

        return SettingsEmailSetResponse(self.user)


class SettingsExtensionCommand(UserCommand):
    def execute(self, bot, message, extension=None):
        if not extension or extension not in BOOK_EXTENSION_CHOICES:
            return SettingsExtensionChooseResponse()

        self.user.extension = extension
        self.user.next_message_is_email = False
        self.user.save()

        return SettingsExtensionSetResponse(extension)


class SearchCommand(UserCommand):
    def __init__(self, index):
        self.index = index

    def execute(self, bot, message, search_term):
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

        if self.user.extension is None:
            return SettingsExtensionCommand().handle(bot, message)

        ebook = book.ebook_mobi
        self.website.download_file(ebook)

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

        book = self.index.get(book_id)
        if not book:
            return BookNotFoundResponse()

        if self.user.extension is None:
            return SettingsExtensionCommand().handle(bot, message)
        if self.user.email is None:
            return SettingsEmailChooseCommand().handle(bot, message)

        try:
            self.mailer.send(book, self.user)
        except Exception as error:
            logging.error(
                "Failed sending email: {}".format(error), exc_info=True)
            return EmailFailedResponse(self.user)
        else:
            return EmailSentResponse(self.user)
