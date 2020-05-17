from unittest import TestCase
from unittest.mock import patch, Mock

from faker import Faker
from telegram.parsemode import ParseMode

from tamizdat.models import (
    BOOK_EXTENSION_CHOICES, make_database,
    Author, Book, User)
from tamizdat.response import (
    NewUserAdminNotification, SettingsResponse,
    SettingsExtensionChooseResponse, SettingsExtensionSetResponse,
    SettingsEmailSetResponse, SearchResponse)


fake = Faker()


class ResponseTestCase(TestCase):
    def setUp(self):
        self.bot = Mock()
        self.message = Mock()
        self.database = make_database()
        self.user = User.create(
            user_id=fake.random.randint(100, 1000000),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            username=fake.word())


class NewUserAdminNotificationTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.admins = [
            User.create(
                user_id=fake.random.randint(100, 1000000),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                username=fake.word(),
                is_admin=True)
            for _ in range(5)
        ]
        self.response = NewUserAdminNotification(self.user)

    def test_str_contains_user_id_and_authorization_command(self):
        text = str(self.response)
        self.assertIn(str(self.user.user_id), text)
        self.assertIn("/authorize{}".format(self.user.user_id), text)

    def test_response_sent_only_to_admins(self):
        self.response.serve(self.bot, self.message)
        for admin in self.admins:
            self.bot.send_message.assert_any_call(
                admin.user_id,
                str(self.response),
                parse_mode=ParseMode.MARKDOWN)


class SettingsResponseTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.user.email = fake.email()
        self.user.extension = fake.random.choice(BOOK_EXTENSION_CHOICES)
        self.response = SettingsResponse(self.user)

    def test_settings_response_mentions_user_format_and_email(self):
        text = str(self.response)
        self.assertIn(self.user.email, text)
        self.assertIn(self.user.extension, text)

    def test_settings_response_shows_two_buttons(self):
        self.response.serve(self.bot, self.message)

        args, kwargs = tuple(self.message.reply_text.call_args)
        inline_keyboard = kwargs["reply_markup"]["inline_keyboard"]
        callbacks = [
            button["callback_data"]
            for row in inline_keyboard
            for button in row
        ]
        self.assertEqual(set(callbacks), set(["/setextension", "/setemail"]))


class SettingsExtensionChooseResponseTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.response = SettingsExtensionChooseResponse()

    def test_extension_dialog_shows_button_for_every_extension(self):
        self.response.serve(self.bot, self.message)

        args, kwargs = tuple(self.message.reply_text.call_args)
        inline_keyboard = kwargs["reply_markup"]["inline_keyboard"]
        callbacks = [
            button["callback_data"]
            for row in inline_keyboard
            for button in row
        ]
        self.assertEqual(set(callbacks), set([
            "/setextension {}".format(extension)
            for extension in BOOK_EXTENSION_CHOICES
        ]))


class SettingsExtensionSetResponseTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.extension = fake.random.choice(BOOK_EXTENSION_CHOICES)
        self.response = SettingsExtensionSetResponse(self.extension)

    def test_extension_dialog_mentions_extension(self):
        self.assertIn(self.extension, str(self.response))


class SettingsEmailSetResponseTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.email = fake.email()
        self.response = SettingsEmailSetResponse(self.email)

    def test_extension_dialog_mentions_extension(self):
        self.assertIn(self.email, str(self.response))


class SearchResponseTestCase(ResponseTestCase):
    def setUp(self):
        super().setUp()
        self.books = []
        for _ in range(5):
            book = Book(
                book_id=fake.random.randint(100, 1000000),
                title=fake.sentence(),
                subtitle=fake.sentence(),
                year=fake.random.randint(1990, 2020),
                series=fake.sentence(),
                language="ru")
            author = Author(
                author_id=fake.random.randint(100, 1000000),
                first_name=fake.first_name(),
                last_name=fake.last_name())
            book.authors.add(author)
        self.response = SearchResponse(self.books)

    def test_minimal_book_info_is_shown_in_search_result(self):
        text = str(self.response)
        for book in self.books:
            print(list(book.authors))
            self.assertIn(book.title, text)
            self.assertIn(book.subtitle, text)
            self.assertIn(book.authors[0].first_name, text)
            self.assertIn(book.authors[0].last_name, text)
            self.assertIn(str(book.year), text)
            self.assertIn(book.series, text)
