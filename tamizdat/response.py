import logging

from jinja2 import Environment, PackageLoader, select_autoescape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.parsemode import ParseMode
from transliterate import translit

from .models import User
from .settings import EMAIL_LOGIN


ICON_BOOK_PILE = "📖"
ICON_ENVELOPE = "✉"


environment = Environment(
    autoescape=select_autoescape(["markdown"]),
    loader=PackageLoader("tamizdat", "templates"),
    lstrip_blocks=True,
    trim_blocks=True)


class NoResponse:
    def serve(self, bot, message):
        pass


class Response:
    template_path = NotImplemented

    def __init__(self):
        self.template = environment.get_template(self.template_path)

    def __str__(self):
        return self.template.render()

    def serve(self, _bot, message):
        return message.reply_text(str(self), parse_mode=ParseMode.HTML)


class UserNotFoundResponse(Response):
    template_path = "user_not_found.html"


class UserAuthorizedResponse(Response):
    template_path = "user_authorized.html"


class NewUserAdminNotification(Response):
    template_path = "new_user.html"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user).strip()

    def serve(self, bot, message):
        admins = User.select().where(User.is_admin == True)
        for admin in admins:
            bot.send_message(
                admin.user_id,
                str(self),
                parse_mode=ParseMode.HTML)


class BookNotFoundResponse(Response):
    template_path = "book_not_found.html"


class SettingsResponse(Response):
    template_path = "settings.html"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user).strip()

    def serve(self, bot, message):
        message.reply_text(
            str(self),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} Указать адрес".format(ICON_ENVELOPE),
                    callback_data="/setemail")
            ]]))


class SettingsEmailChooseResponse(Response):
    template_path = "settings_email_choose.html"


class SettingsEmailSetResponse(Response):
    template_path = "settings_email_set.html"

    def __init__(self, email):
        super().__init__()
        self.email = email

    def __str__(self):
        return self.template.render(bot_email=EMAIL_LOGIN, email=self.email)


class SettingsEmailInvalidResponse(Response):
    template_path = "settings_email_invalid.html"


class SearchResponse(Response):
    template_path = "search_results.html"

    def __init__(self, books):
        super().__init__()
        self.books = books

    def __str__(self):
        return self.template.render(books=self.books).strip()


class BookInfoResponse(Response):
    template_path = "book_info.html"

    def __init__(self, book):
        super().__init__()
        self.book = book

    def __str__(self):
        return self.template.render(book=self.book).strip()

    def serve(self, bot, message):
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
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} Скачать".format(ICON_BOOK_PILE),
                    callback_data="/download {}".format(self.book.book_id)),
                InlineKeyboardButton(
                    "{} Почтой".format(ICON_ENVELOPE),
                    callback_data="/email {}".format(self.book.book_id))
            ]]))


class DownloadResponse(Response):
    template_path = "filename.html"

    def __init__(self, book):
        super().__init__()
        self.book = book
        self.ebook = book.ebook_epub

    def serve(self, bot, message):
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
    template_path = "email_sent.html"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user)


class EmailFailedResponse(Response):
    template_path = "email_failed.html"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user)
