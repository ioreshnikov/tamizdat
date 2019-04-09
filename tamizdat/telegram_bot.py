from telegram.ext import (
    Filters, Updater,
    CallbackQueryHandler, MessageHandler, RegexHandler)

from .command import SearchCommand, BookInfoCommand, DownloadCommand


class TelegramBot:
    def __init__(self, token, index, website):
        self.updater = Updater(token)
        self.updater.dispatcher.add_handler(
            MessageHandler(
                filters=Filters.text,
                callback=SearchCommand(index).handle_message))
        self.updater.dispatcher.add_handler(
            RegexHandler(
                pattern=r"^/info(\d+)",
                callback=BookInfoCommand(index, website).handle_regexp,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            RegexHandler(
                pattern=r"^/download(\d+)",
                callback=DownloadCommand(index, website).handle_regexp,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/download(\d+)",
                callback=DownloadCommand(index, website).handle_regexp,
                pass_groups=True))

    def serve(self):
        self.updater.start_polling()
        self.updater.idle()
