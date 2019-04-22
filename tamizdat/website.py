import logging
from os import path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from lxml import html
import requests

from .models import BOOK_EXTENSION_CHOICES, Book, File


XPATH_ANNOTATION_TEXT = "//h2[text()='Аннотация']/following-sibling::p//text()"

XPATH_COVER_IMAGE_URL = "//img[@title='Cover image']/@src"

XPATH_DOWNLOAD_LINKS = "//a[text()='(читать)']/following-sibling::a/@href"


class Website:
    def __init__(
        self,
        baseurl: str = "http://flibusta.net",
        book_url_format: str = "{baseurl}/b/{id}",
        encoding: str = "utf-8",
        requests: object = requests
    ):
        self.baseurl = baseurl
        self.book_url_format = book_url_format
        self.encoding = encoding
        self.requests = requests

    @staticmethod
    def _get_extension(href: str) -> Optional[str]:
        *_, extension = path.split(href)
        if extension in BOOK_EXTENSION_CHOICES:
            return extension
        return None

    @staticmethod
    def _join_paragraph(sentences: List[str]) -> str:
        return " ".join([
            sentence.strip() for sentence in sentences
        ])

    def _url(self, relative_url: str) -> str:
        return urljoin(self.baseurl, relative_url)

    def _scrape_additional_info(
        self, page_source: str
    ) -> Tuple[str, str, Dict[str, str]]:
        etree = html.fromstring(page_source)

        annotation_text = etree.xpath(XPATH_ANNOTATION_TEXT)
        cover_image_url = etree.xpath(XPATH_COVER_IMAGE_URL)
        download_links = etree.xpath(XPATH_DOWNLOAD_LINKS)

        annotation_text = (
            self._join_paragraph(annotation_text)
            if annotation_text
            else None)

        cover_image_url = (
            self._url(cover_image_url[0])
            if cover_image_url
            else None)

        download_links = {
            self._get_extension(link): link
            for link in download_links
            if self._get_extension(link)
        }

        return annotation_text, cover_image_url, download_links

    def _append_additional_info(
        self,
        book: Book,
        info: Tuple[str, str, Dict[str, str]]
    ) -> Book:
        logging.info(
            "Appending additional info for book_id={}"
            .format(book.book_id))

        annotation, cover_image_url, download_links = info

        if annotation:
            logging.debug("Setting annotation")
            book.annotation = annotation

        if cover_image_url:
            logging.debug("Setting cover image")
            cover_image = File(remote_url=cover_image_url)
            cover_image.save()
            book.cover_image = cover_image

        for extension, url in download_links.items():
            logging.debug("Setting {} ebook".format(extension))
            ebook = File(
                remote_url=url,
                local_path="{}.{}".format(book.book_id, extension))
            ebook.save()
            setattr(book, "ebook_{}".format(extension), ebook)

    def fetch_additional_info(self, book: Book) -> Book:
        if book.augmented:
            logging.debug(
                "Book has all the additional info. "
                "No need to fetch anything.")
            return book

        url = self.book_url_format.format(
            baseurl=self.baseurl,
            id=book.book_id)

        logging.info(
            "Fetching additional info for book_id={}"
            .format(book.book_id))

        with self.requests.get(url) as response:
            info = self._scrape_additional_info(response.text)
            self._append_additional_info(book, info)

        book.augmented = True
        book.save()

    def download(self, url: str, filename: str):
        url = self._url(url)

        logging.debug("Saving {} to {}".format(url, filename))
        with requests.get(url) as response:
            with open(filename, "wb") as fd:
                fd.write(response.content)

    def download_file(self, file_: File):
        remote_url = file_.remote_url
        local_path = file_.local_path

        if not local_path or not path.exists(local_path):
            logging.debug("We don't have the file on disk.")
            self.download(remote_url, local_path)
            logging.debug("File downloaded!")
            file_.save()
