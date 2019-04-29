from unittest import TestCase
from unittest.mock import patch, Mock

from faker import Faker

from tamizdat.command import (
    get_or_create_user,
    SettingsCommand,
    SettingsEmailChooseCommand,
    SettingsEmailSetCommand,
    SettingsExtensionCommand,
    SearchCommand,
    MessageCommand,
    BookInfoCommand,
    DownloadCommand,
    EmailCommand)
from tamizdat.models import BOOK_EXTENSION_CHOICES, make_database, User


fake = Faker()


class GetOrCreateUserTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

        self.chat = Mock()
        self.chat.id = fake.random.randint(0, 1000000)
        self.chat.username = fake.word()
        self.chat.first_name = fake.first_name()
        self.chat.last_name = fake.last_name()

    def test_user_created_if_not_exists(self):
        user = get_or_create_user(self.chat)
        self.assertEqual(user.user_id, self.chat.id)
        self.assertEqual(user.username, self.chat.username)
        self.assertEqual(user.first_name, self.chat.first_name)
        self.assertEqual(user.last_name, self.chat.last_name)

    def test_user_found_if_exists(self):
        User.create(
            user_id=self.chat.id,
            username=self.chat.username,
            first_name=self.chat.first_name,
            last_name=self.chat.last_name)
        user = get_or_create_user(self.chat)
        self.assertEqual(user.user_id, self.chat.id)
        self.assertEqual(user.username, self.chat.username)
        self.assertEqual(user.first_name, self.chat.first_name)
        self.assertEqual(user.last_name, self.chat.last_name)

    def test_user_names_updated_if_does_not_match(self):
        User.create(
            user_id=self.chat.id,
            username=self.chat.username,
            first_name=fake.first_name(),
            last_name=fake.last_name())
        user = get_or_create_user(self.chat)
        self.assertEqual(user.user_id, self.chat.id)
        self.assertEqual(user.username, self.chat.username)
        self.assertEqual(user.first_name, self.chat.first_name)
        self.assertEqual(user.last_name, self.chat.last_name)


class SettingsCommandTestCase(TestCase):
    def setUp(self):
        self.bot = Mock()
        self.update = Mock()

        self.command = SettingsCommand()

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsResponse")
    def test_settings_command_returns_settings_reponse(self, MockResponse, get_or_create_user):
        user = Mock()
        get_or_create_user.return_value = user
        self.command.handle_message(self.bot, self.update)
        MockResponse(user).serve.assert_called_with(self.bot, self.update.message)


class SettingsEmailChooseCommandTestCase(TestCase):
    def setUp(self):
        self.bot = Mock()
        self.update = Mock()

        self.command = SettingsEmailChooseCommand()

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsEmailChooseResponse")
    def test_email_choose_command_returns_correct_response_and_sets_the_flag(self, MockResponse, get_or_create_user):
        user = Mock()
        get_or_create_user.return_value = user
        self.command.handle_command(self.bot, self.update, ())
        self.assertTrue(user.next_message_is_email)
        user.save.assert_called()
        MockResponse().serve.assert_called_with(self.bot, self.update.message)


class SettingsEmailSetCommandTestCase(TestCase):
    def setUp(self):
        self.bot = Mock()
        self.update = Mock()

        self.command = SettingsEmailSetCommand()

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsEmailInvalidResponse")
    def test_invalid_email_sends_the_invalid_response(self, MockResponse, mock_get_or_create_user):
        self.update.message.text = fake.word()
        self.command.handle_message(self.bot, self.update)
        MockResponse().serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.validate_email")
    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsEmailSetResponse")
    def test_settings_email_drops_the_flag_and_sets_the_email(self, MockResponse, mock_get_or_create_user, validate_email):
        user = Mock()
        user.next_message_is_email = True
        mock_get_or_create_user.return_value = user
        validate_email.return_value = True

        self.update.message.text = fake.email()
        self.command.handle_message(self.bot, self.update)
        self.assertFalse(user.next_message_is_email)
        user.save.assert_called()


class SettingsExtensionCommandTestCase(TestCase):
    def setUp(self):
        self.bot = Mock()
        self.update = Mock()

        self.command = SettingsExtensionCommand()

    @patch("tamizdat.command.SettingsExtensionChooseResponse")
    def test_setting_invalid_extension_asks_to_choose_again(self, MockResponse):
        extension = fake.word()
        self.command.handle_callback(self.bot, self.update, (extension, ))
        MockResponse().serve.assert_called_with(self.bot, self.update.callback_query.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsExtensionSetResponse")
    def test_setting_valid_extension_sets_extension(self, MockResponse, mock_get_or_create_user):
        extension = fake.random.choice(BOOK_EXTENSION_CHOICES)
        user = Mock()
        user.next_message_is_email = True

        mock_get_or_create_user.return_value = user
        self.command.handle_callback(self.bot, self.update, (extension, ))

        self.assertFalse(user.next_message_is_email)
        MockResponse(extension).serve.assert_called_with(self.bot, self.update.callback_query.message)


class SearchCommandTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

        self.bot = Mock()
        self.update = Mock()

        self.index = Mock()
        self.command = SearchCommand(self.index)

    @patch("tamizdat.command.SearchResponse")
    def test_search_command_returns_result_if_found(self, MockResponse):
        self.index.search.return_value = Mock()  # Anything but None
        self.update.message.text = fake.sentence()

        self.command.handle_message(self.bot, self.update)

        MockResponse().serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.NotFoundResponse")
    def test_search_command_returns_not_found_if_not_found(self, MockResponse):
        self.index.search.return_value = None
        self.update.message.text = fake.sentence()

        self.command.handle_message(self.bot, self.update)

        MockResponse().serve.assert_called_with(self.bot, self.update.message)


class MessageCommandTestCase(TestCase):
    def setUp(self):
        self.index = Mock()

        self.bot = Mock()
        self.update = Mock()

        with patch("tamizdat.command.SearchCommand") as MockSearchCommand, \
             patch("tamizdat.command.SettingsEmailSetCommand") as MockSettingsEmailSetCommand:
            self.command = MessageCommand(self.index)

    @patch("tamizdat.command.get_or_create_user")
    def test_if_flag_is_not_set_execute_search_command(self, mock_get_or_create_user):
        user = Mock()
        user.next_message_is_email = False
        mock_get_or_create_user.return_value = user
        self.command.handle_message(self.bot, self.update)
        self.command.search_command.execute.assert_called_with(
            self.bot, self.update.message, self.update.message.text)

    @patch("tamizdat.command.get_or_create_user")
    def test_if_flag_is_set_execute_set_email_command(self, mock_get_or_create_user):
        user = Mock()
        user.next_message_is_email = True
        mock_get_or_create_user.return_value = user
        self.command.handle_message(self.bot, self.update)
        self.command.settings_email_set_command.execute.assert_called_with(
            self.bot, self.update.message, self.update.message.text)


class BookInfoCommandTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

        self.bot = Mock()
        self.update = Mock()

        self.index = Mock()
        self.website = Mock()
        self.command = BookInfoCommand(self.index, self.website)

    @patch("tamizdat.command.BookInfoResponse")
    def test_info_command_returns_book_info_if_found(self, MockResponse):
        book_id = fake.random.randint(100, 100000)
        book = Mock()  # Anything but None
        self.index.get.return_value = book

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))

        self.index.get.assert_called_with(book_id)
        self.website.fetch_additional_info.assert_called_with(book)
        MockResponse(book).serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.NotFoundResponse")
    def test_info_command_returns_not_found_if_not_found(self, MockResponse):
        book_id = fake.random.randint(100, 100000)
        book = None
        self.index.get.return_value = book

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))

        self.index.get.assert_called_with(book_id)
        MockResponse().serve.assert_called_with(self.bot, self.update.message)


class DownloadCommandTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

        self.bot = Mock(0)
        self.update = Mock()

        self.index = Mock()
        self.website = Mock()
        self.command = DownloadCommand(self.index, self.website)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.DownloadResponse")
    def test_download_command_downloads_a_book_if_found(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 100000)
        book = Mock()
        self.index.get.return_value = book

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))
        self.website.download_file.assert_called_with(book.ebook_mobi)
        MockResponse(book).serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.NotFoundResponse")
    def test_download_command_returns_not_found_if_not_found(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 100000)
        self.index.get.return_value = None

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))
        MockResponse().serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.DownloadResponse")
    def test_download_callback_downloads_a_book_if_found(self, MockResponse, mock_get_or_create_user):
        self.test_download_command_downloads_a_book_if_found()

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.NotFoundResponse")
    def test_download_callback_returns_not_found_if_not_found(self, MockResponse, mock_get_or_create_user):
        self.test_download_command_returns_not_found_if_not_found()


class EmailCommandTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

        self.bot = Mock()
        self.update = Mock()

        self.index = Mock()
        self.website = Mock()
        self.mailer = Mock()
        self.command = EmailCommand(self.index, self.website, self.mailer)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.EmailSentResponse")
    def test_email_command_sends_email_if_found(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()
        user = Mock()
        mock_get_or_create_user.return_value = user
        self.index.get.return_value = book

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))
        self.mailer.send.assert_called_with(book, user)
        MockResponse(user).serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.EmailFailedResponse")
    def test_email_command_returns_failure_message_if_failed(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()
        user = Mock()
        mock_get_or_create_user.return_value = user
        self.index.get.return_value = book
        self.mailer.send.side_effect = Mock(side_effect=RuntimeError())

        self.command.handle_command_regex(self.bot, self.update, (book_id, ))
        MockResponse().serve.assert_called_with(self.bot, self.update.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.EmailSentResponse")
    def test_email_callback_sends_email_if_found(self, MockResponse, mock_get_or_create_user):
        # The same as test_email_comamnd_sends_email_if_found, but with a callback.
        book_id = fake.random.randint(100, 1000000)
        book = Mock()
        user = Mock()
        mock_get_or_create_user.return_value = user
        self.index.get.return_value = book

        self.command.handle_callback_regex(self.bot, self.update, (book_id, ))
        self.mailer.send.assert_called_with(book, user)
        MockResponse(user).serve.assert_called_with(self.bot, self.update.callback_query.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsExtensionChooseResponse")
    def test_email_callback_asks_for_extension_if_none(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()
        user = Mock()
        user.extension = None
        mock_get_or_create_user.return_value = user
        self.index.get.return_value = book

        self.command.handle_callback_regex(self.bot, self.update, (book_id, ))
        MockResponse().serve.assert_called_with(self.bot, self.update.callback_query.message)

    @patch("tamizdat.command.get_or_create_user")
    @patch("tamizdat.command.SettingsEmailChooseResponse")
    def test_email_callback_asks_for_email_if_none(self, MockResponse, mock_get_or_create_user):
        book_id = fake.random.randint(100, 1000000)
        book = Mock()
        user = Mock()
        user.extension = fake.random.choice(BOOK_EXTENSION_CHOICES)
        user.email = None
        mock_get_or_create_user.return_value = user
        self.index.get.return_value = book

        self.command.handle_callback_regex(self.bot, self.update, (book_id, ))
        MockResponse().serve.assert_called_with(self.bot, self.update.callback_query.message)
