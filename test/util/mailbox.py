import imaplib
import smtplib
import ssl
from email.mime.text import MIMEText


class Mailbox:
    def __init__(self, app_domain, domain, user, password):
        self.app_domain = app_domain
        self.address = '{0}@{1}'.format(user, domain)
        self.user = user
        self.password = password

    def send(self, subject):
        server = smtplib.SMTP(self.app_domain, 587, timeout=10)
        server.ehlo()
        server.starttls(context=self.context())
        server.ehlo()
        server.login(self.user, self.password)
        message = MIMEText('body of {0}'.format(subject))
        message['Subject'] = subject
        message['From'] = self.address
        message['To'] = self.address
        server.send_message(message)
        server.quit()

    def context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def imap(self):
        server = imaplib.IMAP4_SSL(self.app_domain, ssl_context=self.context())
        server.login(self.user, self.password)
        return server

    def count(self, folder):
        server = self.imap()
        try:
            status, data = server.select(folder, readonly=True)
            assert status == 'OK', data
            return int(data[0])
        finally:
            server.logout()

    def flags(self, folder, subject):
        server = self.imap()
        try:
            server.select(folder, readonly=True)
            _, data = server.search(None, 'SUBJECT', '"{0}"'.format(subject))
            ids = data[0].split()
            assert len(ids) == 1, '{0}: {1}'.format(subject, ids)
            _, fetched = server.fetch(ids[0], '(FLAGS)')
            return fetched[0].decode()
        finally:
            server.logout()
