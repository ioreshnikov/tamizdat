import logging

from jinja2 import Environment, PackageLoader, select_autoescape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.parsemode import ParseMode
from transliterate import translit

from .models import BOOK_EXTENSION_CHOICES
from .settings import EMAIL_LOGIN


ICON_BOOK_PILE = "📖"
ICON_ENVELOPE = "✉"
ICONS_BOOK_EXTENSIONS = ("📔", "📕", "📓")


environment = Environment(
    autoescape=select_autoescape(["markdown"]),
    loader=PackageLoader("tamizdat", "templates"),
    lstrip_blocks=True,
    trim_blocks=True)


class Response:
    template = None

    def __init__(self):
        self.template = environment.get_template(self.template)

    def __str__(self):
        return self.template.render()

    def serve(self, bot, message):
        return message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class NotFoundResponse(Response):
    template = "not_found.md"


class SettingsResponse(Response):
    template = "settings.md"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user).strip()

    def serve(self, bot, message):
        message.reply_text(
            str(self),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} Выбрать формат".format(ICON_BOOK_PILE),
                    callback_data="/setextension"),
                InlineKeyboardButton(
                    "{} Указать адрес".format(ICON_ENVELOPE),
                    callback_data="/setemail")
            ]]))


class SettingsExtensionChooseResponse(Response):
    template = "settings_extension_choose.md"

    def serve(self, bot, message):
        buttons = zip(ICONS_BOOK_EXTENSIONS, BOOK_EXTENSION_CHOICES)
        message.reply_text(
            str(self),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "{} {}".format(icon, extension),
                    callback_data="/setextension {}".format(extension))
                for icon, extension in buttons
            ]]))


class SettingsExtensionSetResponse(Response):
    template = "settings_extension_set.md"

    def __init__(self, extension):
        super().__init__()
        self.extension = extension

    def __str__(self):
        return self.template.render(extension=self.extension)


class SettingsEmailChooseResponse(Response):
    template = "settings_email_choose.md"


class SettingsEmailSetResponse(Response):
    template = "settings_email_set.md"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(bot_email=EMAIL_LOGIN, user=self.user)


class SettingsEmailInvalidResponse(Response):
    template = "settings_email_invalid.md"


class SearchResponse(Response):
    template = "search_results.md"

    def __init__(self, books):
        super().__init__()
        self.books = books

    def __str__(self):
        return self.template.render(books=self.books).strip()


class BookInfoResponse(Response):
    template = "book_info.md"

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
    template = "filename.md"

    def __init__(self, book):
        super().__init__()
        self.book = book
        self.ebook = book.ebook_mobi

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
    template = "email_sent.md"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user)


class EmailFailedResponse(Response):
    template = "email_failed.md"

    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return self.template.render(user=self.user)
