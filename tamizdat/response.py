import logging

from jinja2 import Environment, PackageLoader, select_autoescape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.bot import Bot
from telegram.message import Message
from telegram.parsemode import ParseMode
from transliterate import translit

from .models import BOOK_EXTENSION_CHOICES, Book, User
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
    template_path = NotImplemented

    def __init__(self):
        self.template = environment.get_template(self.template_path)

    def __str__(self):
        return self.template.render()

    def serve(self, bot: Bot, message: Message) -> None:
        return message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class NotFoundResponse(Response):
    template_path = "not_found.md"


class SettingsResponse(Response):
    template_path = "settings.md"

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def __str__(self) -> str:
        return self.template.render(user=self.user).strip()

    def serve(self, bot: Bot, message: Message) -> None:
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
    template_path = "settings_extension_choose.md"

    def serve(self, bot: Bot, message: Message) -> None:
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
    template_path = "settings_extension_set.md"

    def __init__(self, extension: str):
        super().__init__()
        self.extension = extension

    def __str__(self) -> str:
        return self.template.render(extension=self.extension)


class SettingsEmailChooseResponse(Response):
    template_path = "settings_email_choose.md"


class SettingsEmailSetResponse(Response):
    template_path = "settings_email_set.md"

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def __str__(self) -> str:
        return self.template.render(bot_email=EMAIL_LOGIN, user=self.user)


class SettingsEmailInvalidResponse(Response):
    template_path = "settings_email_invalid.md"


class SearchResponse(Response):
    template_path = "search_results.md"

    def __init__(self, books: Book):
        super().__init__()
        self.books = books

    def __str__(self) -> str:
        return self.template.render(books=self.books).strip()


class BookInfoResponse(Response):
    template_path = "book_info.md"

    def __init__(self, book: Book):
        super().__init__()
        self.book = book

    def __str__(self) -> str:
        return self.template.render(book=self.book).strip()

    def serve(self, bot: Bot, message: Message) -> None:
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
    template_path = "filename.md"

    def __init__(self, book: Book):
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
    template_path = "email_sent.md"

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def __str__(self) -> str:
        return self.template.render(user=self.user)


class EmailFailedResponse(Response):
    template_path = "email_failed.md"

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def __str__(self) -> str:
        return self.template.render(user=self.user)
