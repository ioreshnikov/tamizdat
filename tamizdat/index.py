import logging

from .models import Author, Book, BookAuthors, CardIndex, Card


CATALOG_CSV_COLUMNS = (
    "Last Name",
    "First Name",
    "Middle Name",
    "Title",
    "Subtitle",
    "Language",
    "Year",
    "Series",
    "ID")


CATALOG_DB_COLUMNS = (
    "last_name",
    "first_name",
    "middle_name",
    "title",
    "subtitle",
    "language",
    "year",
    "series",
    "book_id")


class Index:
    def __init__(self, database):
        self.database = database

    @staticmethod
    def _split_line(line):
        return tuple(
            column.strip()
            for column in line.split(";"))

    @staticmethod
    def _proper_header(columns):
        return list(columns) == list(CATALOG_CSV_COLUMNS)

    @staticmethod
    def _proper_record(columns):
        return len(columns) == len(CATALOG_CSV_COLUMNS)

    @staticmethod
    def _prepare_card(columns):
        record = dict(zip(CATALOG_DB_COLUMNS, columns))

        try:
            record["year"] = int(record["year"])
        except ValueError:
            record["year"] = None

        card = Card(**record)
        return card

    def _import_cards(self, catalog):
        logging.debug("Reading the catalog")
        header_line = next(catalog)
        header_columns = self._split_line(header_line)
        assert self._proper_header(header_columns), \
            "unexpected header {}".format(header_line)

        catalog_records = (
            self._split_line(line)
            for line in catalog)

        catalog_cards = (
            self._prepare_card(record)
            for record in catalog_records
            if self._proper_record(record))

        with self.database.atomic():
            logging.debug("Adding the cards")
            peewee_logger = logging.getLogger("peewee")
            peewee_logger.setLevel(logging.INFO)
            Card.bulk_create(catalog_cards, batch_size=1000)
            peewee_logger.setLevel(logging.DEBUG)

    def _prepare_authors(self):
        authors = (
            Card
            .select(
                Card.last_name,
                Card.first_name,
                Card.middle_name)
            .group_by(
                Card.last_name,
                Card.first_name,
                Card.middle_name))

        with self.database.atomic():
            logging.debug("Collecting the authors")
            Author.insert_from(authors, [
                Author.last_name,
                Author.first_name,
                Author.middle_name
            ]).execute()

    def _prepare_books(self):
        books = (
            Card
            .select(
                Card.title,
                Card.subtitle,
                Card.language,
                Card.year,
                Card.series,
                Card.book_id
            ).group_by(Card.book_id))

        cards_authors = (
            Card
            .select(Card.book_id, Author.author_id)
            .join(
                Author, on=(
                    (Card.last_name == Author.last_name) &
                    (Card.first_name == Author.first_name) &
                    (Card.middle_name == Author.middle_name))))

        book_authors = (
            cards_authors
            .select(Card.book_id, Author.author_id))

        with self.database.atomic():
            logging.debug("Collecting the books")
            Book.insert_from(
                books, [
                    Book.title,
                    Book.subtitle,
                    Book.language,
                    Book.year,
                    Book.series,
                    Book.book_id
                ]).execute()

            logging.debug("Cross-referencing the books and the authors")
            BookAuthors.insert_from(
                book_authors, [
                    Book.book_id,
                    Author.author_id
                ]).execute()

    def _prepare_card_index(self):
        cards = Card.select(
            Card.card_id,
            Card.last_name,
            Card.first_name,
            Card.middle_name,
            Card.title,
            Card.subtitle,
            Card.series)

        with self.database.atomic():
            logging.debug("Preparing fulltext index")
            CardIndex.insert_from(
                cards, [
                    CardIndex.rowid,
                    CardIndex.last_name,
                    CardIndex.first_name,
                    CardIndex.middle_name,
                    CardIndex.title,
                    CardIndex.subtitle,
                    CardIndex.series
                ]
            ).execute()

    def import_catalog(self, catalog):
        logging.info("Importing catalog")
        self._import_cards(catalog)
        self._prepare_authors()
        self._prepare_books()
        self._prepare_card_index()
        logging.info("Importing done!")

    def search(self, term, page_number=1, items_per_page=10):
        books = (
            Book
            .select(Book, Card, CardIndex)
            .join(Card, on=(Book.book_id == Card.book_id))
            .join(CardIndex, on=(Card.card_id == CardIndex.rowid))
            .where(CardIndex.match(term))
            .group_by(Book.book_id)
            .paginate(page_number, items_per_page))
        return list(books)

    def get(self, book_id):
        return Book.get_or_none(Book.book_id == book_id)
