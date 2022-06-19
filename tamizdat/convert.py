import logging
import os
import subprocess

from .models import File


def prepare_cover(book):
    """
    Prepare a book cover.

    :param book: a Book instance.
    """
    if not book.cover_image:
        return

    input_path = book.cover_image.local_path
    basename, ext = os.path.splitext(input_path)
    output_path = "{}_cover{}".format(basename, ext)

    subprocess.check_call([
        "convert", input_path,
        "-filter", "lanczos",
        "-resize", "x650",
        output_path
    ])

    return output_path


def convert_book(book):
    """
    Converts an ebook from .fb2.zip to .epub with some extra enhancements.

    :param book: a Book instance.
    """

    if book.ebook_epub is not None and os.path.exists(book.ebook_epub.local_path):
        logging.info("Converted book already exists. Doing nothing.")
        return

    input_path = book.ebook_fb2.local_path
    basename, _ = input_path.split(os.extsep, 1)
    output_path = "{}.epub".format(basename)

    command = [
        "ebook-convert", input_path, output_path,
        "--no-inline-fb2-toc",
        "--sr1-search=(?s)<div><h3>Annotation</h3>.*<div class=\"paragraph\">.*</div>.*</div><hr/>",
        "--sr1-replace=",
        "--output-profile=kindle",
    ]
    cover_path = prepare_cover(book)
    if cover_path:
        command.append("--cover={}".format(cover_path))

    logging.info("Converting {} to {}".format(input_path, output_path))

    subprocess.check_call(command)

    logging.info("Conversion to {} done!".format(output_path))

    book.ebook_epub = File(local_path=output_path)
    book.ebook_epub.save()
    book.save()
