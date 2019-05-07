from telegram.ext import (
    Filters, Updater,
    CallbackQueryHandler, CommandHandler, MessageHandler, RegexHandler)

from .command import (
    AuthorizeUserCommand,
    SettingsCommand, SettingsEmailChooseCommand, SettingsExtensionCommand,
    MessageCommand, BookInfoCommand, DownloadCommand, EmailCommand)


class TelegramBot:
    def __init__(self, token, index, website, mailer):
        self.updater = Updater(token)
        self.updater.dispatcher.add_handler(
            MessageHandler(
                filters=Filters.text,
                callback=MessageCommand(index).handle_message))
        self.updater.dispatcher.add_handler(
            RegexHandler(
                pattern=r"^/authorize(\d+)",
                callback=AuthorizeUserCommand().handle_command_regex,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "settings",
                SettingsCommand().handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "setextension",
                callback=SettingsExtensionCommand().handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/setextension\s*(.*)",
                callback=SettingsExtensionCommand().handle_callback_regex,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "setemail",
                callback=SettingsEmailChooseCommand().handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/setemail",
                callback=SettingsEmailChooseCommand().handle_callback_regex,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "info",
                callback=BookInfoCommand(
                    index, website).handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            RegexHandler(
                pattern=r"^/info(\d+)",
                callback=BookInfoCommand(
                    index, website).handle_command_regex,
                pass_groups=True))
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "download",
                callback=DownloadCommand(
                    index, website).handle_command,
                pass_args=True)),
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/download (\d+)",
                callback=DownloadCommand(
                    index, website).handle_callback_regex,
                pass_groups=True)),
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "email",
                callback=EmailCommand(
                    index, website, mailer).handle_command,
                pass_args=True))
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(
                pattern=r"^/email (\d+)",
                callback=EmailCommand(
                    index, website, mailer).handle_callback_regex,
                pass_groups=True))

    def serve(self):
        self.updater.start_polling()
        self.updater.idle()
