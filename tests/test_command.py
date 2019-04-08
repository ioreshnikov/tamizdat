from unittest import TestCase
from unittest.mock import patch, Mock

from tamizdat.command import (
    SearchCommand,
    BookInfoCommand,
    DownloadCommand)
from tamizdat.models import make_database, Author, Book, File
from tamizdat.response import (
    SearchResponse,
    BookInfoResponse,
    DownloadResponse)


class SearchCommandTestCase(TestCase):
    def test_search_command_performs_search(self):
        index = Mock()
        command = SearchCommand(index)
        response = command.execute("a test search")
        self.assertEqual(index.search.call_args, (("a test search", ), ))
        self.assertIsInstance(response, SearchResponse)


class BookInfoCommandTestCase(TestCase):
    def test_info_command_looks_up_a_book_and_fetches_additional_info(self):
        make_database()
        test_book = Book(book_id=93857, title="Пикник на обочине")
        test_book.save()

        index = Mock()
        website = Mock()
        index.get.return_value = test_book

        command = BookInfoCommand(index, website)
        response = command.execute(test_book.book_id)

        self.assertEqual(index.get.call_args, ((test_book.book_id, ), ))
        self.assertEqual(website.fetch_additional_info.call_args, ((test_book, ), ))
        self.assertIsInstance(response, BookInfoResponse)


class DownloadCommandTestCase(TestCase):
    def make_fake_book(self):
        test_book = Book(book_id=93857, title="Пикник на обочине")

        test_author = Author(
            first_name="Аркадий",
            middle_name="Натанович",
            last_name="Стругацкий")
        test_author.save()

        test_ebook = File(remote_url="/b/93857/mobi")
        test_ebook.save()

        test_book.authors.add(test_author)
        test_book.ebook_mobi = test_ebook
        test_book.save()

        return test_book

    def test_download_command_download_noncached_file(self):
        make_database()

        test_book = self.make_fake_book()

        index = Mock()
        index.get.return_value = test_book
        website = Mock()

        with patch("os.path.exists") as mock:
            mock.return_value = False
            command = DownloadCommand(index, website)
            response = command.execute(test_book.book_id)

        self.assertTrue(website.download_file.called)
        self.assertIsInstance(response, DownloadResponse)

    def test_download_command_does_not_download_cached_file(self):
        make_database()

        test_book = self.make_fake_book()
        test_book.ebook_mobi.local_path = "/just/a/fake/path"

        index = Mock()
        index.get.return_value = test_book
        website = Mock()

        with patch("os.path.exists") as mock:
            mock.return_value = True
            command = DownloadCommand(index, website)
            response = command.execute(test_book.book_id)

        self.assertTrue(website.download_file.called)
        self.assertIsInstance(response, DownloadResponse)
