from peewee import (
    Proxy, SqliteDatabase,
    Model, DeferredThroughModel,
    AutoField, DeferredForeignKey, ForeignKeyField, ManyToManyField,
    BooleanField, CharField, IntegerField, TextField)
from playhouse.sqlite_ext import FTS5Model, SearchField


proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = proxy


class Author(BaseModel):
    class Meta:
        indexes = (
            (("last_name", "first_name", "middle_name"), True),)

    author_id = AutoField(primary_key=True, unique=True)

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

    augmented = BooleanField(null=True, default=False)
    annotation = TextField(null=True)
    cover_image = DeferredForeignKey("File", field="file_id", null=True)
    ebook_epub = DeferredForeignKey("File", field="file_id", null=True)

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

    card_id = AutoField(primary_key=True, unique=True)

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


class File(BaseModel):
    file_id = AutoField()

    remote_url = CharField(null=True)
    local_path = CharField(null=True)
    telegram_id = CharField(null=True)


class User(BaseModel):
    user_id = IntegerField(unique=True)

    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)

    is_admin = BooleanField(default=False)
    is_authorized = BooleanField(default=False)
    next_message_is_email = BooleanField(default=False)

    email = CharField(null=True)


def make_database(address = ":memory:"):
    database = SqliteDatabase(address)
    proxy.initialize(database)
    database.create_tables([
        Author, Book, BookAuthors,
        Card, CardIndex,
        File, User])
    return database
