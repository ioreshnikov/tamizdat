from telegram.ext import (
    Filters, Updater,
    CallbackQueryHandler, CommandHandler, MessageHandler, RegexHandler)

from .command import (
    SetEmailCommand, SetFormatCommand,
    SearchCommand, BookInfoCommand,
    DownloadCommand, EmailCommand)


class TelegramBot:
    def __init__(self, token, index, website, mailer):
        self.updater = Updater(token)
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "email",
                callback=SetEmailCommand().handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "format",
                callback=SetFormatCommand().handle_command,
                pass_args=True))
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
                pass_groups=True)),
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/download(\d+)",
                callback=DownloadCommand(index, website).handle_regexp,
                pass_groups=True)),
        self.updater.dispatcher.add_handler(
            RegexHandler(
                pattern=r"^/email(\d+)",
                callback=EmailCommand(index, website, mailer).handle_regexp,
                pass_groups=True)),
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/email(\d+)",
                callback=EmailCommand(index, website, mailer).handle_regexp,
                pass_groups=True))

    def serve(self):
        self.updater.start_polling()
        self.updater.idle()
