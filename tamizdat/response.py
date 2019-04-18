from jinja2 import Environment, PackageLoader, select_autoescape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.parsemode import ParseMode
from transliterate import translit


environment = Environment(
    autoescape=select_autoescape(["markdown"]),
    loader=PackageLoader("tamizdat", "templates"),
    lstrip_blocks=True,
    trim_blocks=True)


class NotFoundResponse:
    def __str__(self):
        template = environment.get_template("not_found.md")
        return template.render()

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class GetEmailResponse:
    def __init__(self, user):
        self.user = user

    def __str__(self):
        template = environment.get_template("get_email.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class SetEmailResponse:
    def __init__(self, user):
        self.user = user

    def __str__(self):
        template = environment.get_template("set_email.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class GetFormatResponse:
    def __init__(self, user):
        self.user = user

    def __str__(self):
        template = environment.get_template("get_format.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class SetFormatResponse:
    def __init__(self, user):
        self.user = user

    def __str__(self):
        template = environment.get_template("set_format.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class SearchResponse:
    def __init__(self, books):
        self.books = books

    def __str__(self):
        template = environment.get_template("search_results.md")
        return template.render(books=self.books).strip()

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class BookInfoResponse:
    def __init__(self, book):
        self.book = book

    def __str__(self):
        template = environment.get_template("book_info.md")
        return template.render(book=self.book).strip()

    def serve(self, bot, update):
        if self.book.cover_image:
            update.message.reply_photo(self.book.cover_image.remote_url)
        update.message.reply_text(
            str(self),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "📦 Скачать",
                    callback_data="/download{}".format(self.book.book_id)),
                InlineKeyboardButton(
                    "✉ Почтой",
                    callback_data="/email{}".format(self.book.book_id))
            ]]))


class DownloadResponse:
    def __init__(self, book):
        self.book = book
        self.ebook = book.ebook_mobi

    def serve(self, bot, update):
        message = update.message
        if not message:
            message = update.callback_query.message

        if self.ebook.telegram_id:
            return message.reply_document(
                self.ebook.telegram_id)

        template = environment.get_template("filename.md")
        filename = translit(template.render(book=self.book), reversed=True)
        response = message.reply_document(
            document=open(self.ebook.local_path, "rb"),
            filename=filename,
            timeout=60)

        self.ebook.telegram_id = response.document.file_id
        self.ebook.save()


class EmailSentResponse:
    def __init__(self, user):
        self.user = user

    def __str__(self):
        template = environment.get_template("email_sent.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)


class EmailFailedResponse:
    def __str__(self):
        template = environment.get_template("email_sent.md")
        return template.render(user=self.user)

    def serve(self, bot, update):
        update.message.reply_text(str(self), parse_mode=ParseMode.MARKDOWN)
