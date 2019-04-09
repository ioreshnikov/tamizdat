from collections import OrderedDict
from io import StringIO

from faker import Faker


CATALOG_PROPER_HEADER = "Last Name;First Name;Middle Name;Title;Subtitle;Language;Year;Series;ID"
CATALOG_BROKEN_HEADER = "Last Name;First Name;Middle Name;Title;Language;Year;Series;ID"


fake = Faker("ru_RU")


def fake_words(nb_words):
    return " ".join(fake.words(nb_words))


def fake_last_name():
    return fake.last_name_male()


def fake_first_name():
    return fake.first_name_male()


def fake_middle_name():
    return fake.middle_name_male()


def fake_author():
    return OrderedDict(
        last_name=fake_last_name(),
        first_name=fake_first_name(),
        middle_name=fake_middle_name())


def fake_book():
    return OrderedDict(
        title=fake_words(nb_words=3),
        subtitle=fake_words(nb_words=5),
        language=fake.country_code(),
        year=fake.random_int(1900, 2000),
        series=fake_words(nb_words=2),
        book_id=fake.random_int(0, 100000))


def fake_card():
    return OrderedDict(
        last_name=fake.last_name_male(),
        first_name=fake.first_name_male(),
        middle_name=fake.middle_name_male(),
        title=fake_words(nb_words=3),
        subtitle=fake_words(nb_words=5),
        languge=fake.country_code(),
        year=fake.random_int(1900, 2000),
        series=fake_words(nb_words=2),
        book_id=fake.random_int(0, 100000))


def fake_cards(num_cards):
    cards = []
    for _ in range(num_cards):
        card = fake_card()
        cards.append(card)
    return cards


def fake_cards_with_author_duplicates(num_cards):
    num_books = int(num_cards / 2)
    num_authors = 2

    books = [fake_book() for _ in range(num_books)]
    authors = [fake_author() for _ in range(num_authors)]

    cards = []
    for book in books:
        for author in authors:
            card = OrderedDict()
            card.update(author)
            card.update(book)
            cards.append(card)

    return cards


def store_catalog(header, cards):
    catalog = StringIO()
    catalog.write(header + "\n")
    for card in cards:
        catalog.write(";".join(
            str(field) for field in card.values()) + "\n")
    catalog.seek(0)
    return catalog


def fake_catalog(header, num_lines):
    return store_catalog(header, fake_cards(num_lines))


def fake_catalog_with_author_duplicates(header, num_lines):
    return store_catalog(
        header,
        fake_cards_with_author_duplicates(num_lines))
