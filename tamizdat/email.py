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
        host: str,
        port: int,
    ):
        self.host = host
        self.port = port
        self.login = login
        self.password = password

    def prepare_message(self, book, user):
        authors = environment.get_template("authors.md").render(book=book)
        title = book.title
        subject = "{}. {}".format(authors, title)

        message = MIMEMultipart()
        message["From"] = self.login
        message["To"] = user.email
        message["Date"] = formatdate()
        message["Subject"] = subject

        if book.annotation:
            message.attach(MIMEText(book.annotation))

        with open(book.ebook_mobi.local_path, "rb") as fd:
            filename = basename(book.ebook_mobi.local_path)
            attachment = MIMEApplication(
                fd.read(), Name=filename)
            attachment["Content-Disposition"] = (
                "attachment; filename={}".format(filename))
            message.attach(attachment)

        return message

    def send(self, book, user):
        message = self.prepare_message(book, user)
        server = SMTP_SSL(self.host, self.port)

        server.ehlo()
        server.login(self.login, self.password)
        server.sendmail(self.login, user.email, str(message))
        server.close()
