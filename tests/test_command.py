from unittest import TestCase
from unittest.mock import call, patch, Mock

from faker import Faker

from tamizdat.command import (
    AdminCommand,
    UserCommand,
    AuthorizeUserCommand,
    SettingsCommand,
    SettingsEmailChooseCommand,
    SettingsEmailSetCommand,
    SearchCommand,
    MessageCommand,
    BookInfoCommand,
    DownloadCommand,
    EmailCommand)
from tamizdat.models import make_database, User


fake = Faker()


class UserCommandTestMixin:
    def setUp(self):
        self.update = Mock()
        self.context = Mock()
        self.context.args = ()

    def run(self, *args, **kwargs):
        self.user = Mock()
        with patch("tamizdat.command.UserCommand.get_user") as self.mock_get_user:
            self.mock_get_user.return_value = self.user
            super().run(*args, **kwargs)


class UserCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = UserCommand()

    @patch("tamizdat.command.NewUserAdminNotification")
    def test_handling_with_nonexistent_user_creates_user_and_notifies_user(self, MockResponse):
        self.mock_get_user.return_value = None

        self.update.message.chat.id = fake.random.randint(100, 1000000)
        self.update.message.chat.first_name = fake.first_name()
        self.update.message.chat.last_name = fake.last_name()
        self.update.message.chat.username = fake.word()

        self.command.handle_message(self.update, self.context)
        user = User.get_or_none(user_id=self.update.message.chat.id)

        self.assertFalse(user.is_authorized)
        self.assertEqual(user.first_name, self.update.message.chat.first_name)
        self.assertEqual(user.last_name, self.update.message.chat.last_name)
        self.assertEqual(user.username, self.update.message.chat.username)

        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.NoResponse")
    def test_handling_with_unauthorized_user_does_nothing(self, MockResponse):
        self.user.is_authorized = False
        self.command.handle_message(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class AdminCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = AdminCommand()

    @patch("tamizdat.command.NoResponse")
    def test_handling_with_non_admin_user_does_nothing(self, MockResponse):
        self.user.is_admin = False
        self.command.handle_message(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class AuthorizeUserCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = AuthorizeUserCommand()

    @patch("tamizdat.command.NoResponse")
    def test_command_from_non_admin_is_ignored(self, MockResponse):
        user_id = fake.random.randint(100, 1000000)

        self.mock_get_user.return_value = None
        self.context.match.groups.return_value = (user_id, )

        self.command.handle_command_regex(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.UserNotFoundResponse")
    def test_authorizing_nonexistent_user_is_not_possible(self, MockResponse):
        user_id = fake.random.randint(100, 1000000)
        self.mock_get_user.side_effect = [
            Mock(),
            None
        ]
        self.context.match.groups.return_value = (user_id, )

        self.command.handle_command_regex(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.UserAuthorizedResponse")
    def test_authorizing_user_changes_status(self, MockResponse):
        user = Mock()
        user_id = fake.random.randint(100, 1000000)

        self.mock_get_user.return_value = user
        self.context.match.groups.return_value = (user_id, )

        self.command.handle_command_regex(self.update, self.context)
        self.assertTrue(user.is_authorized)
        user.save.assert_called_with()
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class SettingsCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = SettingsCommand()

    @patch("tamizdat.command.SettingsResponse")
    def test_settings_command_returns_settings_reponse(self, MockResponse):
        self.command.handle_command(self.update, self.context)
        MockResponse(self.user).serve.assert_called_with(self.context.bot, self.update.message)


class SettingsEmailChooseCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = SettingsEmailChooseCommand()

    @patch("tamizdat.command.SettingsEmailChooseResponse")
    def test_email_choose_command_returns_correct_response_and_sets_the_flag(self, MockResponse):
        self.command.handle_command(self.update, self.context)
        self.assertTrue(self.user.next_message_is_email)
        self.user.save.assert_called()
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class SettingsEmailSetCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.command = SettingsEmailSetCommand()

    @patch("tamizdat.command.SettingsEmailInvalidResponse")
    def test_invalid_email_sends_the_invalid_response(self, MockResponse):
        self.update.message.text = fake.word()
        self.command.handle_message(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.validate_email")
    @patch("tamizdat.command.SettingsEmailSetResponse")
    def test_settings_email_drops_the_flag_and_sets_the_email(
            self, MockResponse, validate_email):
        self.user.next_message_is_email = True
        validate_email.return_value = True

        self.update.message.text = fake.email()
        self.command.handle_message(self.update, self.context)
        self.assertFalse(self.user.next_message_is_email)
        self.user.save.assert_called()


class SearchCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.database = make_database()
        self.index = Mock()
        self.command = SearchCommand(self.index)

    @patch("tamizdat.command.SearchResponse")
    def test_search_command_returns_result_if_found(self, MockResponse):
        self.index.search.return_value = Mock()  # Anything but None
        self.update.message.text = fake.sentence()

        self.command.handle_message(self.update, self.context)

        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.BookNotFoundResponse")
    def test_search_command_returns_not_found_if_not_found(self, MockResponse):
        self.index.search.return_value = None
        self.update.message.text = fake.sentence()

        self.command.handle_message(self.update, self.context)

        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class MessageCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.index = Mock()
        with patch("tamizdat.command.SearchCommand") as MockSearchCommand, \
             patch("tamizdat.command.SettingsEmailSetCommand") as MockSettingsEmailSetCommand:
            self.command = MessageCommand(self.index)

    def test_if_flag_is_not_set_execute_search_command(self):
        self.user.next_message_is_email = False

        self.command.handle_message(self.update, self.context)
        self.command.search_command.handle.assert_called_with(
            self.context.bot, self.update.message, self.update.message.text)

    def test_if_flag_is_set_execute_set_email_command(self):
        self.user.next_message_is_email = True

        self.command.handle_message(self.update, self.context)
        self.command.settings_email_set_command.handle.assert_called_with(
            self.context.bot, self.update.message, self.update.message.text)


class BookInfoCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.database = make_database()
        self.index = Mock()
        self.website = Mock()
        self.command = BookInfoCommand(self.index, self.website)

    @patch("tamizdat.command.BookInfoResponse")
    def test_info_command_returns_book_info_if_found(self, MockResponse):
        book_id = fake.random.randint(100, 100000)
        book = Mock()  # Anything but None

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)

        self.index.get.assert_called_with(book_id)
        self.website.fetch_additional_info.assert_called_with(book)
        MockResponse(book).serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.BookNotFoundResponse")
    def test_info_command_returns_not_found_if_not_found(self, MockResponse):
        book_id = fake.random.randint(100, 100000)
        book = None

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)

        self.index.get.assert_called_with(book_id)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)


class DownloadCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.database = make_database()
        self.index = Mock()
        self.website = Mock()
        self.command = DownloadCommand(self.index, self.website)

    @patch("tamizdat.command.convert_book")
    @patch("tamizdat.command.DownloadResponse")
    def test_download_command_downloads_a_book_if_found(self, MockResponse, mock_convert_book):
        book_id = fake.random.randint(100, 100000)
        book = Mock()

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)

        self.website.download_file.assert_has_calls(
            [call(book.ebook_fb2), call(book.cover_image)])
        mock_convert_book.assert_called_with(book)

        MockResponse(book).serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.BookNotFoundResponse")
    def test_download_command_returns_not_found_if_not_found(self, MockResponse):
        book_id = fake.random.randint(100, 100000)

        self.index.get.return_value = None
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.convert_book")
    @patch("tamizdat.command.DownloadResponse")
    def test_download_command_skips_cover_if_not_defined(self, MockResponse, mock_convert_book):
        book_id = fake.random.randint(100, 100000)
        book = Mock()
        book.cover_image = None

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)

        # A clunky way to assert that something _was not_ called.
        with self.assertRaises(AssertionError):
            self.website.download_file.assert_called_with(book.cover_image)
        mock_convert_book.assert_called_with(book)

        MockResponse(book).serve.assert_called_with(self.context.bot, self.update.message)


class EmailCommandTestCase(UserCommandTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.database = make_database()
        self.index = Mock()
        self.website = Mock()
        self.mailer = Mock()
        self.command = EmailCommand(self.index, self.website, self.mailer)

    @patch("tamizdat.command.DownloadCommand")
    @patch("tamizdat.command.EmailSentResponse")
    def test_email_command_sends_email_if_found(self, MockResponse, MockDownloadCommand):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_command_regex(self.update, self.context)
        self.mailer.send.assert_called_with(book, self.user)
        MockResponse(self.user).serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.DownloadCommand")
    @patch("tamizdat.command.EmailFailedResponse")
    def test_email_command_returns_failure_message_if_failed(self, MockResponse, MockDownloadCommand):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )
        self.mailer.send.side_effect = Mock(side_effect=RuntimeError())

        self.command.handle_command_regex(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.message)

    @patch("tamizdat.command.DownloadCommand")
    @patch("tamizdat.command.EmailSentResponse")
    def test_email_callback_sends_email_if_found(self, MockResponse, MockDownloadCommand):
        # The same as test_email_comamnd_sends_email_if_found, but with a callback.
        book_id = fake.random.randint(100, 1000000)
        book = Mock()

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.command.handle_callback_regex(self.update, self.context)
        self.mailer.send.assert_called_with(book, self.user)
        MockResponse(self.user).serve.assert_called_with(self.context.bot, self.update.callback_query.message)

    @patch("tamizdat.command.SettingsEmailChooseResponse")
    def test_email_callback_asks_for_email_if_none(self, MockResponse):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()

        self.index.get.return_value = book
        self.context.match.groups.return_value = (book_id, )

        self.user.email = None

        self.command.handle_callback_regex(self.update, self.context)
        MockResponse().serve.assert_called_with(self.context.bot, self.update.callback_query.message)
