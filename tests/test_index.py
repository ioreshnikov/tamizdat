import random
from unittest import TestCase

from tamizdat.index import Index
from tamizdat.models import (
    make_database,
    Author, Book, BookAuthors, CardIndex, Card)

from .fixtures import (
    CATALOG_BROKEN_HEADER, CATALOG_PROPER_HEADER,
    fake_card, fake_cards, fake_cards_with_author_duplicates,
    store_catalog, fake_catalog, fake_catalog_with_author_duplicates)


class IndexTestCase(TestCase):
    def setUp(self):
        self.database = make_database()
        self.catalog = Index(self.database)

    def test_proper_header_is_proper(self):
        columns = Index._split_line(CATALOG_PROPER_HEADER)
        self.assertTrue(Index._proper_header(columns))

    def test_broken_header_is_not_proper(self):
        columns = Index._split_line(CATALOG_BROKEN_HEADER)
        self.assertFalse(Index._proper_header(columns))

    def test_fake_record_is_proper(self):
        self.assertTrue(Index._proper_record(fake_card()))

    def test_fake_record_with_missing_field_is_not_proper(self):
        record = list(fake_card().values())
        short_record = record[1:]
        self.assertFalse(Index._proper_record(short_record))

    def test_prepare_card_returns_card(self):
        record = fake_card().values()
        card = Index._prepare_card(record)
        self.assertIsInstance(card, Card)
        self.assertIsNotNone(card.title)
        self.assertIsNotNone(card.book_id)

    def test_importing_cards_from_proper_catalog(self):
        catalog = fake_catalog(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.assertEqual(Card.select().count(), 10)

    def test_importing_card_from_broken_catalog(self):
        catalog = fake_catalog(CATALOG_BROKEN_HEADER, 10)
        with self.assertRaises(AssertionError):
            self.catalog._import_cards(catalog)

    def test_preparing_authors_from_imported_cards_without_duplicates(self):
        catalog = fake_catalog(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.assertEqual(Author.select().count(), 10)

    def test_preparing_authors_from_imported_cards_with_author_duplicates(self):
        catalog = fake_catalog_with_author_duplicates(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.assertLess(Author.select().count(), 10)

    def test_preparing_books_from_imported_cards_without_duplicates(self):
        catalog = fake_catalog(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.catalog._prepare_books()
        self.assertEqual(Book.select().count(), 10)
        self.assertEqual(Author.select().count(), 10)
        self.assertEqual(BookAuthors.select().count(), 10)

    def test_preparing_books_from_imported_cards_with_author_duplicates(self):
        catalog = fake_catalog_with_author_duplicates(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.catalog._prepare_books()
        self.assertLess(Book.select().count(), 10)
        self.assertLess(Author.select().count(), 10)
        self.assertEqual(BookAuthors.select().count(), 10)

    def test_preparing_index_from_imported_cards_without_duplicates(self):
        catalog = fake_catalog(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.catalog._prepare_books()
        self.catalog._prepare_card_index()

        self.assertEqual(Book.select().count(), 10)
        self.assertEqual(Author.select().count(), 10)
        self.assertEqual(BookAuthors.select().count(), 10)
        self.assertEqual(CardIndex.select().count(), 10)

    def test_preparing_index_from_imported_cards_with_author_duplicates(self):
        catalog = fake_catalog_with_author_duplicates(CATALOG_PROPER_HEADER, 10)
        self.catalog._import_cards(catalog)
        self.catalog._prepare_authors()
        self.catalog._prepare_books()
        self.catalog._prepare_card_index()
        self.assertLess(Book.select().count(), 10)
        self.assertLess(Author.select().count(), 10)
        self.assertEqual(BookAuthors.select().count(), 10)
        self.assertEqual(CardIndex.select().count(), 10)

    def test_simple_search(self):
        cards = fake_cards(10)
        catalog = store_catalog(CATALOG_PROPER_HEADER, cards)

        self.catalog.import_catalog(catalog)
        random_card = random.choice(cards)
        random_title = random_card["title"]

        search_result = self.catalog.search(random_title)
        self.assertIsInstance(search_result, list)
        self.assertEqual(len(search_result), 1)
        self.assertEqual(search_result[0].title, random_title)

    def test_search_with_author_duplicates(self):
        cards = fake_cards_with_author_duplicates(10)
        catalog = store_catalog(CATALOG_PROPER_HEADER, cards)

        self.catalog.import_catalog(catalog)
        random_card = random.choice(cards)
        random_title = random_card["title"]

        search_result = self.catalog.search(random_title)
        self.assertIsInstance(search_result, list)
        self.assertEqual(len(search_result), 1)
        self.assertEqual(search_result[0].title, random_title)
