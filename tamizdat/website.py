import logging
from os import path
from urllib.parse import urljoin

from lxml import html
import requests

from .models import File


XPATH_ANNOTATION_TEXT = "//h2[text()='Аннотация']/following-sibling::p//text()"

XPATH_COVER_IMAGE_URL = "//img[@title='Cover image']/@src"

XPATH_DOWNLOAD_LINKS = "//a[text()='(читать)']/following-sibling::a/@href"


class Website:
    def __init__(
        self,
        baseurl="http://flibusta.net",
        book_url_format="{baseurl}/b/{id}",
        encoding="utf-8",
        requests=requests
    ):
        self.baseurl = baseurl
        self.book_url_format = book_url_format
        self.encoding = encoding
        self.requests = requests

    @staticmethod
    def _get_extension(href):
        *_, extension = path.split(href)
        return extension

    @staticmethod
    def _join_paragraph(sentences):
        return " ".join([
            sentence.strip() for sentence in sentences
        ])

    def _url(self, relative_url):
        return urljoin(self.baseurl, relative_url)

    def _scrape_additional_info(self, page_source):
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

        ebook_url = None
        for link in download_links:
            if self._get_extension(link) == "epub":
                ebook_url = link

        return annotation_text, cover_image_url, ebook_url

    def _append_additional_info(self, book, info):
        logging.info(
            "Appending additional info for book_id={}"
            .format(book.book_id))

        annotation, cover_image_url, ebook_url = info

        if annotation:
            logging.debug("Setting annotation")
            book.annotation = annotation

        if cover_image_url:
            logging.debug("Setting cover image")
            _, ext = path.splitext(cover_image_url)
            cover_image = File(
                remote_url=cover_image_url,
                local_path="{}{}".format(book.book_id, ext))
            cover_image.save()
            book.cover_image = cover_image

        logging.debug("Setting ebook")
        ebook = File(
            remote_url=ebook_url,
            local_path="{}.epub".format(book.book_id))
        ebook.save()
        book.ebook_epub = ebook

    def fetch_additional_info(self, book):
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

    def download(self, url, filename):
        url = self._url(url)

        logging.debug("Saving {} to {}".format(url, filename))
        with requests.get(url) as response:
            with open(filename, "wb") as fd:
                fd.write(response.content)

    def download_file(self, file_):
        remote_url = file_.remote_url
        local_path = file_.local_path

        if not local_path or not path.exists(local_path):
            logging.debug("We don't have the file on disk.")
            self.download(remote_url, local_path)
            logging.debug("File downloaded!")
            local_path = file_.local_path
            file_.save()
