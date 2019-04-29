from .models import Book, User

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename
from smtplib import SMTP_SSL

from tamizdat.response import environment


class Mailer:
    def __init__(
        self,
        login: str,
        password: str,
        host: str = "stmp.google.com",
        port: int = 587,
    ):
        self.host = host
        self.port = port
        self.login = login
        self.password = password

    def prepare_message(self, book: Book, user: User) -> MIMEMultipart:
        authors = environment.get_template("authors.md").render(book=book)
        title = book.title
        subject = "{}. {}".format(authors, title)

        message = MIMEMultipart()
        message["From"] = self.login
        message["To"] = user.email
        message["Date"] = formatdate()
        message["Subject"] = subject

        message.attach(MIMEText(book.annotation))

        ebook = book.ebook_mobi
        with open(ebook.local_path, "rb") as fd:
            filename = basename(ebook.local_path)
            attachment = MIMEApplication(
                fd.read(), Name=filename)
            attachment["Content-Disposition"] = (
                "attachment; filename={}".format(filename))
            message.attach(attachment)

        return message

    def send(self, book: Book, user: User) -> None:
        message = self.prepare_message(book, user)
        server = SMTP_SSL(self.host, self.port)

        server.ehlo()
        server.login(self.login, self.password)
        server.sendmail(self.login, user.email, str(message))
        server.close()
