from peewee import (
    Proxy, SqliteDatabase,
    Model, DeferredThroughModel,
    AutoField, ForeignKeyField, ManyToManyField,
    CharField, IntegerField)
from playhouse.sqlite_ext import FTS5Model, SearchField


proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = proxy


class Author(BaseModel):
    class Meta:
        indexes = (
            (("last_name", "first_name", "middle_name"), True),)

    author_id = AutoField(primary_key=True)

    last_name = CharField(null=True)
    first_name = CharField(null=True)
    middle_name = CharField(null=True)

    def __repr__(self):
        return "Author({}, {}, {})".format(
            self.last_name,
            self.first_name,
            self.middle_name)

    def __str__(self):
        return repr(self)


BookAuthorsDeferred = DeferredThroughModel()


class Book(BaseModel):
    book_id = IntegerField(index=True)

    title = CharField()
    subtitle = CharField(null=True)
    language = CharField(null=True)
    year = IntegerField(null=True)
    series = CharField(null=True)

    authors = ManyToManyField(
        Author,
        backref="books",
        through_model=BookAuthorsDeferred)

    def __repr__(self):
        return "Book({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, ...)".format(
            self.book_id,
            self.title,
            self.subtitle,
            self.language,
            self.year,
            self.series)

    def __str__(self):
        return repr(self)


class BookAuthors(BaseModel):
    book_id = ForeignKeyField(Book, field="book_id")
    author_id = ForeignKeyField(Author, field="author_id")


BookAuthorsDeferred.set_model(BookAuthors)


class Card(BaseModel):
    class Meta:
        indexes = (
            (("book_id",), False),
            (("last_name", "first_name", "middle_name"), False))

    card_id = AutoField(primary_key=True)

    last_name = CharField(null=True)
    first_name = CharField(null=True)
    middle_name = CharField(null=True)
    title = CharField()
    subtitle = CharField(null=True)
    language = CharField(null=True)
    year = IntegerField(null=True)
    series = CharField(null=True)
    book_id = IntegerField()

    def __repr__(self):
        return (
            "Card({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})"
            .format(
                self.last_name,
                self.first_name,
                self.middle_name,
                self.title,
                self.subtitle,
                self.language,
                self.year,
                self.series,
                self.book_id))

    def __str__(self):
        return repr(self)


class CardIndex(FTS5Model):
    class Meta:
        database = proxy

    last_name = SearchField()
    first_name = SearchField()
    middle_name = SearchField()
    title = SearchField()
    subtitle = SearchField()
    series = SearchField()

    def __repr__(self):
        return "CardIndex({!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.last_name,
            self.first_name,
            self.middle_name,
            self.title,
            self.subtitle,
            self.series)

    def __str__(self):
        return repr(self)


def make_database(address: str = ":memory:") -> SqliteDatabase:
    database = SqliteDatabase(address)
    proxy.initialize(database)
    database.create_tables([Author, Book, BookAuthors, Card, CardIndex])
    return database
