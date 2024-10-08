from unittest import TestCase
from unittest.mock import patch, MagicMock

from tamizdat.models import make_database, Book, File
from tamizdat.website import Website


def read_saved_page(book_id):
    filename = "tests/assets/{}.html".format(book_id)
    with open(filename) as fd:
        return fd.read()


def mock_head(url, *args, **kwargs):
    mock_response = MagicMock()
    mock_response.url = url
    return mock_response


class WebsiteTestCase(TestCase):
    def setUp(self):
        self.database = make_database()
        self.website = Website(requests=MagicMock())

    def test_get_extension(self):
        self.assertEqual(self.website._get_extension("/b/485688/epub"), "epub")
        self.assertEqual(self.website._get_extension("/b/485688/fb2"), "fb2")
        self.assertEqual(self.website._get_extension("/b/485688/mobi"), "mobi")
        self.assertEqual(self.website._get_extension("/b/485688/"), "")

    def test_join_paragraph(self):
        sentences = [
            "Все счастливые семьи похожи друг на друга, \n",
            "каждая несчастливая семья несчастлива по-своему."
        ]
        expected = (
            "Все счастливые семьи похожи друг на друга, "
            "каждая несчастливая семья несчастлива по-своему.")
        self.assertEqual(self.website._join_paragraph(sentences), expected)

    def test_scraping_info_from_a_webpage(self):
        self.website.requests.head = mock_head

        page_source = read_saved_page("93872")
        info = self.website._scrape_additional_info(page_source)
        annotation, cover, ebook = info

        self.assertIsNotNone(annotation)
        self.assertTrue(cover.endswith("jpg"))
        self.assertTrue(ebook.endswith("epub"))

    def test_appending_additional_info(self):
        self.website.requests.head = mock_head

        page_source = read_saved_page("93872")
        info = self.website._scrape_additional_info(page_source)

        book = Book(book_id=93872, title="Трудно быть богом")
        book.save()

        self.assertIsNone(book.annotation)
        self.assertIsNone(book.cover_image)
        self.assertIsNone(book.ebook_epub)

        self.website._append_additional_info(book, info)

        self.assertIsNotNone(book.annotation)

        self.assertIsInstance(book.cover_image, File)
        self.assertTrue(book.cover_image.remote_url.endswith(".jpg"))

        self.assertIsInstance(book.ebook_epub, File)
        self.assertTrue(book.ebook_epub.remote_url.endswith("/epub"))
        self.assertTrue(book.ebook_epub.local_path.endswith(".epub"))
