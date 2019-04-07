from unittest import TestCase

from tamizdat.models import make_database, Author, Book, Card

from .fixtures import fake_author, fake_book, fake_card


class ModelTestCase(TestCase):
    def setUp(self):
        self.database = make_database()

    def test_create_author(self):
        author_inserted = Author(**fake_author())
        self.assertEqual(author_inserted.save(), 1)

        author_selected = Author.get(
            Author.author_id == author_inserted.author_id)
        self.assertEqual(author_inserted, author_selected)

    def test_create_book(self):
        book_inserted = Book(**fake_book())
        self.assertEqual(book_inserted.save(), 1)

        book_selected = Book.get(
            Book.book_id == book_inserted.book_id)
        self.assertEqual(book_inserted, book_selected)

    def test_create_book_with_one_author(self):
        author = Author(**fake_author())
        author.save()

        book_inserted = Book(**fake_book())
        book_inserted.authors.add(author)
        book_inserted.save()

        book_selected = Book.get(
            Book.book_id == book_inserted.book_id)

        self.assertEqual(book_inserted, book_selected)
        self.assertEqual(book_selected.authors[0], author)
        self.assertEqual(author.books[0], book_selected)

    def test_create_book_with_two_authors(self):
        author1 = Author(**fake_author())
        author2 = Author(**fake_author())
        author1.save()
        author2.save()

        book_inserted = Book(**fake_book())
        book_inserted.authors.add(author1)
        book_inserted.authors.add(author2)
        book_inserted.save()

        book_selected = Book.get(
            Book.book_id == book_inserted.book_id)

        self.assertEqual(book_inserted, book_selected)
        self.assertEqual(list(book_selected.authors), [author1, author2])
        self.assertEqual(author1.books[0], book_selected)
        self.assertEqual(author2.books[0], book_selected)

    def test_create_card(self):
        card_inserted = Card(**fake_card())
        self.assertEqual(card_inserted.save(), 1)

        card_selected = Card.get(Card.card_id, card_inserted.card_id)
        self.assertEqual(card_inserted, card_selected)

        card_selected = Card.get(Card.book_id, card_inserted.book_id)
        self.assertEqual(card_inserted, card_selected)
