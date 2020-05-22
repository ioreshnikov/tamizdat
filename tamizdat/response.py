"""
Responses
---------

This module defines the bot responses.

:author: Ivan Oreshnikov <oreshnikov.ivan@gmail.com>
"""


import logging

from jinja2 import Environment, PackageLoader, select_autoescape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.parsemode import ParseMode
from transliterate import translit

from .models import User
from .settings import EMAIL_LOGIN


ICON_BOOK_PILE = "📖"
"""Icon shown on the download button."""
ICON_ENVELOPE = "✉"
"""Icon shown on the email button."""


environment = Environment(
    autoescape=select_autoescape(["markdown"]),
    loader=PackageLoader("tamizdat", "templates"),
    lstrip_blocks=True,
    trim_blocks=True)


class NoResponse:
    """
    An empty response.  Usually not rendered at all but used to signal
    to :meth:`Command.handle` that the execution should be aborted.
    """

    def serve(self, bot, message):
        pass


class Response:
    """
    A base class for bot responses.
    """

    template_path = NotImplemented

    def __init__(self):
        """Instantiate the response."""
        self.template = environment.get_template(self.template_path)

    def __str__(self):
        """Render the response."""
        return self.template.render()

    def serve(self, bot, message):
        """Serve the response."""
        return message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class UserNotFoundResponse(Response):
    """
    Indicate that the user is not in the database.
    """
    template_path = "user_not_found.md"


class UserAuthorizedResponse(Response):
    """
    User has been successfully authorized.
    """
    template_path = "user_authorized.md"


class NewUserAdminNotification(Response):
    """
    Indicate to the adiministrator that a new user has been added to
    the database.
    """
    template_path = "new_user.md"

    def __init__(self, user):
        """
        Instantiate the command.

        :param user: newly authorized user.
        :type user: :class:`model.User`
        """
        super().__init__()
        self.user = user

    def __str__(self):
        """Render the response."""
        return self.template.render(user=self.user).strip()

    def serve(self, bot, message):
        """Serve the response."""
        admins = User.select().where(User.is_admin == True)
        for admin in admins:
            bot.send_message(
                admin.user_id,
                str(self),
                parse_mode=ParseMode.MARKDOWN)


class BookNotFoundResponse(Response):
    """
    Indicate that the book is not in the database.
    """
    template_path = "book_not_found.md"


class SettingsResponse(Response):
    """
    Show the user settings.
    """
    template_path = "settings.md"

    def __init__(self, user):
        """
        Instantiate the response.

        :param user: the user whos settings should be shown.
        :type user: :class:`model.User`
        """
        super().__init__()
        self.user = user

    def __str__(self):
        """Render the response."""
        return self.template.render(user=self.user).strip()

    def serve(self, bot, message):
        """Serve the response."""
        message.reply_text(
            str(self),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} Указать адрес".format(ICON_ENVELOPE),
                    callback_data="/setemail")
            ]]))


class SettingsEmailChooseResponse(Response):
    """
    Query the user for a new email.
    """
    template_path = "settings_email_choose.md"


class SettingsEmailSetResponse(Response):
    """
    Indicate that the email has been accepted.
    """
    template_path = "settings_email_set.md"

    def __init__(self, email):
        """
        Instantiate the command.

        :param str email: the accepted email.
        """
        super().__init__()
        self.email = email

    def __str__(self):
        """Render the response."""
        return self.template.render(bot_email=EMAIL_LOGIN, email=self.email)


class SettingsEmailInvalidResponse(Response):
    """
    Indicate that the email is not valid.
    """
    template_path = "settings_email_invalid.md"


class SearchResponse(Response):
    """
    Render the search results.
    """
    template_path = "search_results.md"

    def __init__(self, books):
        """
        Instantiate the response.

        :param books: the list of the books corresponding to the
            search query.
        :type books: a list of :class:`tamizdat.model.Book`.
        """
        super().__init__()
        self.books = books

    def __str__(self):
        return self.template.render(books=self.books).strip()


class BookInfoResponse(Response):
    """
    Display the information about a single book.
    """
    template_path = "book_info.md"

    def __init__(self, book):
        """
        Instantiate the response.

        :param book: the book.
        :type book: class:`tamizdat.model.Book`.
        """
        super().__init__()
        self.book = book

    def __str__(self):
        """Render the response."""
        return self.template.render(book=self.book).strip()

    def serve(self, bot, message):
        """Serve the response."""
        if self.book.cover_image:
            try:
                logging.debug(
                    "Trying to send cover image {}"
                    .format(self.book.cover_image.remote_url))
                message.reply_photo(self.book.cover_image.remote_url)
            except TelegramError as error:
                logging.error(error, exc_info=True)

        message.reply_text(
            str(self),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} Скачать".format(ICON_BOOK_PILE),
                    callback_data="/download {}".format(self.book.book_id)),
                InlineKeyboardButton(
                    "{} Почтой".format(ICON_ENVELOPE),
                    callback_data="/email {}".format(self.book.book_id))
            ]]))


class DownloadResponse(Response):
    """
    Serve the downloaded book.
    """
    template_path = "filename.md"

    def __init__(self, book):
        """
        Instantiate the response.

        :param book: the book.
        :type book: class:`tamizdat.model.Book`.
        """
        super().__init__()
        self.book = book
        self.ebook = book.ebook_mobi

    def serve(self, bot, message):
        """Serve the response."""
        if self.ebook.telegram_id:
            return message.reply_document(
                self.ebook.telegram_id)

        filename = translit(
            self.template.render(book=self.book),
            reversed=True)
        response = message.reply_document(
            document=open(self.ebook.local_path, "rb"),
            filename=filename,
            timeout=60)

        self.ebook.telegram_id = response.document.file_id
        self.ebook.save()


class EmailSentResponse(Response):
    """
    Indicate that the response has been sent.
    """
    template_path = "email_sent.md"

    def __init__(self, user):
        """
        Instantiate the response.

        :param user: the message recipient.
        :type user: :class:`tamizdat.model.User`
        """
        super().__init__()
        self.user = user

    def __str__(self):
        """Render the response."""
        return self.template.render(user=self.user)


class EmailFailedResponse(Response):
    """
    Report that the email has not been sent.  Currently it's also used
    for generic error reporting so we probably should rename it.
    """
    template_path = "email_failed.md"

    def __init__(self, user):
        """
        Instantiate the response.

        :param user: the message recipient.
        :type user: :class:`tamizdat.model.User`
        """
        super().__init__()
        self.user = user

    def __str__(self):
        """Render the response."""
        return self.template.render(user=self.user)
