"""
Commands
--------

This module defines the commands executed by the bot.

:author: Ivan Oreshnikov <oreshnikov.ivan@gmail.com>
"""

import logging
import string

from validate_email import validate_email

from .convert import convert_book
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


class Command:
    """
    A base class for all commands performed by the bot.
    """

    def prepare(self, bot, message):
        """
        A pre-hook executed before the handling the request.  This
        method should be defined in a subclass.

        :param bot: the bot receiving the message.
        :param message: the incoming message.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        pass

    def execute(self, bot, message, *args):
        """
        This method defines the main actios executed by the command.
        This method need to be declared in a subclass.

        :param bot: the bot receiving the message.
        :param message: the incoming message.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        raise NotImplementedError()

    def handle(self, bot, message, *args):
        """
        Run the prepare hook and then execute the command.  Normally
        you don't need to call this function directly.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param tuple args: additional arguments passed to :meth:`execute`.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        response = self.prepare(bot, message)
        if response:
            return response
        return self.execute(bot, message, *args)

    def handle_message(self, update, context):
        """
        This method unpacks the update and passes the message text to
        :meth:`handle`.

        :param update: an update received by the bot.
        :param context: the request context.

        :type update: :class:`telegram.Update`
        :type context: :class:`telegram.Context`
        """
        message = update.message
        response = self.handle(context.bot, message, message.text)
        return response.serve(context.bot, message)

    def handle_command(self, update, context):
        """
        This method unpacks the update and passes the command
        arguments to :meth:`handle`.

        :param update: an update received by the bot.
        :param context: the request context.

        :type update: :class:`telegram.Update`
        :type context: :class:`telegram.Context`
        """
        message = update.message
        response = self.handle(context.bot, message, *context.args)
        return response.serve(context.bot, message)

    def handle_callback(self, update, context):
        """
        This method unpacks the update and passes the callback
        arguments to :meth:`handle`.

        :param update: an update received by the bot.
        :param context: the request context.

        :type update: :class:`telegram.Update`
        :type context: :class:`telegram.Context`
        """
        message = update.callback_query.message
        response = self.handle(context.bot, message, *context.args)
        return response.serve(context.bot, message)

    def handle_command_regex(self, update, context):
        """
        This method unpacks the update and passes the regex match
        groups to :meth:`handle`.

        :param update: an update received by the bot.
        :param context: the request context.

        :type update: :class:`telegram.Update`
        :type context: :class:`telegram.Context`
        """
        message = update.message
        response = self.handle(context.bot, message, *context.match.groups())
        return response.serve(context.bot, message)

    def handle_callback_regex(self, update, context):
        """
        This method unpacks the update and passes the regex match
        groups to :meth:`handle`.

        :param update: an update received by the bot.
        :param context: the request context.

        :type update: :class:`telegram.Update`
        :type context: :class:`telegram.Context`
        """
        message = update.callback_query.message
        response = self.handle(context.bot, message, *context.match.groups())
        return response.serve(context.bot, message)


class UserCommand(Command):
    """
    The base class for commands permitted only for the authorized
    users.
    """

    def get_user(self, user_id):
        """
        Find the user in the database by id.

        :param int user_id: telegram user id.
        """
        return User.get_or_none(User.user_id == user_id)

    def prepare(self, bot, message):
        """
        Try to find the user in the database.  If the user is not
        found create a new unauthorized user and then notify the
        adminisrator.  If the user is not authorized then keep silent
        but not execute the command.

        :param bot: the bot receiving the message.
        :param message: the incoming message.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
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
    """
    The base class for commands permitted only to the administrators.
    """

    def prepare(self, bot, message):
        """
        Try to find the user in the database.  If the user is not an
        administrator, then keep silent but not execute the command.
        """
        user = self.get_user(user_id=message.chat.id)
        if not user or not user.is_admin:
            return NoResponse()

        self.user = user


class AuthorizeUserCommand(AdminCommand):
    """
    Authorize a newly created user.
    """

    def execute(self, bot, message, user_id):
        """
        Authorize a newly created user.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param int user_id: the user id to be authorized.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """

        user = self.get_user(user_id)
        if not user:
            return UserNotFoundResponse()

        user.is_authorized = True
        user.save()

        return UserAuthorizedResponse()


class SettingsCommand(UserCommand):
    """
    Display user settings.
    """

    def execute(self, bot, message):
        """
        Display user settings.

        :param bot: the bot receiving the message.
        :param message: the incoming message.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        return SettingsResponse(self.user)


class SettingsEmailChooseCommand(UserCommand):
    """
    Query user for email.
    """

    def execute(self, bot, message):
        """
        Query user for email.

        :param bot: the bot receiving the message.
        :param message: the incoming message.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        self.user.next_message_is_email = True
        self.user.save()

        return SettingsEmailChooseResponse()


class SettingsEmailSetCommand(UserCommand):
    """
    Either accept or decline new user email.
    """

    def execute(self, bot, message, email):
        """
        Either accept or decline new user email.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str email: the new email.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        if not validate_email(email):
            return SettingsEmailInvalidResponse()

        self.user.email = email
        self.user.next_message_is_email = False
        self.user.save()

        return SettingsEmailSetResponse(self.user.email)


class SearchCommand(UserCommand):
    """
    Search for books in the database.
    """

    def __init__(self, index):
        """
        Instantiate the command.

        :param index: the database index object.
        :type index: :class:`tamizdat.index.Index`.
        """
        self.index = index
        self.translator = str.maketrans(dict.fromkeys(string.punctuation))

    def execute(self, bot, message, search_term):
        """
        Either accept or decline new user email.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str search_term: search term.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        search_term = search_term.translate(self.translator)
        books = self.index.search(search_term)
        if not books:
            return BookNotFoundResponse()
        return SearchResponse(books)


class MessageCommand(UserCommand):
    """
    Process the message depending whether we have queried a new email
    or not.

    .. note::
    Probably we should refactor the email query command such that this
    wrapper is not necessary.
    """

    def __init__(self, index):
        """
        Instantiate the command.

        :param index: the database index object.
        :type index: :class:`tamizdat.index.Index`.
        """
        self.search_command = SearchCommand(index)
        self.settings_email_set_command = SettingsEmailSetCommand()

    def execute(self, bot, message, text):
        """
        If we're in the email queyry loop (that is determined by a
        user flag) then treat the message as an email.  Otherwise
        perform a search.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str search_term: search term.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        if self.user.next_message_is_email:
            return self.settings_email_set_command.handle(bot, message, text)
        else:
            return self.search_command.handle(bot, message, text)


class BookInfoCommand(UserCommand):
    """
    Show the book info.
    """

    def __init__(self, index, website):
        """
        Instantiate the command.

        :param index: the database index object.
        :param webiste: the website object.

        :type index: :class:`tamizdat.index.Index`
        :type website: :class:`tamizdat.website.Website`
        """
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        """
        Show the book info.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str book_id: book id in the database.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        book = self.index.get(book_id)
        if not book:
            return BookNotFoundResponse()
        self.website.fetch_additional_info(book)
        return BookInfoResponse(book)


class DownloadCommand(UserCommand):
    """
    Download the book.
    """

    def __init__(self, index, website):
        """
        Instantiate the command.

        :param index: the database index object.
        :param webiste: the website object.

        :type index: :class:`tamizdat.index.Index`
        :type website: :class:`tamizdat.website.Website`
        """
        self.index = index
        self.website = website

    def execute(self, bot, message, book_id):
        """
        Download the book.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str book_id: book id in the database.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
        book = self.index.get(book_id)
        if not book:
            return BookNotFoundResponse()

        logging.info("Asked for ebook for book_id={}".format(book_id))
        try:
            self.website.download_file(book.ebook_fb2)
            if book.cover_image:
                self.website.download_file(book.cover_image)
            convert_book(book)
        except Exception as error:
            logging.error(
                "Failed to download file: {}".format(error), exc_info=True)
            return EmailFailedResponse(self.user)
        else:
            return DownloadResponse(book)


class EmailCommand(UserCommand):
    """
    Send the book by email.
    """

    def __init__(self, index, website, mailer):
        """
        Instantiate the command.

        :param index: the database index object.
        :param webiste: the website object.
        :param mailer: the mailer object.

        :type index: :class:`tamizdat.index.Index`
        :type website: :class:`tamizdat.website.Website`
        :type mailer: :class:`tamizdat.email.Mailer`
        """
        self.index = index
        self.website = website
        self.mailer = mailer

    def execute(self, bot, message, book_id):
        """
        Download the book.

        :param bot: the bot receiving the message.
        :param message: the incoming message.
        :param str book_id: book id in the database.

        :type bot: :class:`telegram.Bot`
        :type message: :class:`telegram.Message`
        """
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
