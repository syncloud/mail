import imaplib
import json
import re
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from os.path import dirname, join
from subprocess import check_output

import pytest
from syncloudlib.integration.hosts import add_host_alias

from test.util.helper import retry_func

TMP_DIR = '/tmp/syncloud'
POSTFIX_REVISION = 463
USERS = {
    'alice': 'Alice-Password1',
    'bob': 'Bob-Password1',
}
REMOVED_USER = 'carl'
REMOVED_PASSWORD = 'Carl-Password1'
LIST_LINE = re.compile(r'\((?P<flags>[^)]*)\) (?:"[^"]*"|NIL) (?P<name>.+)$')
COUNTS_FILE = join(dirname(__file__), '..', 'build', 'mail-counts-before-upgrade.json')


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('journalctl > {0}/upgrade-prev.journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('find /var/snap/mail/current/box > {0}/upgrade-prev.box.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/upgrade-prev.*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain, device):
    add_host_alias(app, device_host, domain)
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)


def test_install_postfix_release(device):
    device.run_ssh('snap remove mail')
    device.run_ssh('snap install mail --revision={0}'.format(POSTFIX_REVISION), retries=3)
    assert 'dovecot' in device.run_ssh('snap services mail')


@pytest.mark.parametrize('user', list(USERS.keys()) + [REMOVED_USER])
def test_add_user(device, user):
    output = device.run_ssh('snap run platform.cli user add {0} --password {1} --email {0}@external.example'.format(
        user, password(user)))
    assert 'added' in output, output


@pytest.mark.parametrize('user', USERS.keys())
def test_send_mail(app_domain, domain, user):
    for subject in ['migrated-{0}-inbox'.format(user), 'migrated-{0}-project'.format(user),
                    'migrated-{0}-unread'.format(user)]:
        retry_func(lambda: send_as(app_domain, domain, user, subject), message='send ' + subject, retries=10, sleep=5)
    retry_func(lambda: assert_count(app_domain, user, 'INBOX', 3), message='delivery to ' + user, retries=30, sleep=3)


@pytest.mark.parametrize('user', USERS.keys())
def test_organize_mail(app_domain, user):
    server = imap(app_domain, user)
    try:
        assert server.create('Projects')[0] == 'OK'
        server.select('INBOX')
        project = only(server, 'migrated-{0}-project'.format(user))
        assert server.copy(project, 'Projects')[0] == 'OK'
        assert server.store(project, '+FLAGS', '(\\Deleted)')[0] == 'OK'
        server.expunge()
        inbox = only(server, 'migrated-{0}-inbox'.format(user))
        assert server.store(inbox, '+FLAGS', '(\\Flagged \\Seen)')[0] == 'OK'
    finally:
        server.logout()
    assert_count(app_domain, user, 'Projects', 1)
    assert_count(app_domain, user, 'INBOX', 2)


@pytest.mark.parametrize('user', USERS.keys())
def test_sent_mail(app_domain, domain, user):
    server = imap(app_domain, user)
    try:
        status, _ = server.select('Sent')
        if status != 'OK':
            assert server.create('Sent')[0] == 'OK'
        message = MIMEText('a reply that was sent')
        message['Subject'] = 'migrated-{0}-sent'.format(user)
        message['From'] = '{0}@{1}'.format(user, domain)
        message['To'] = 'someone@example.com'
        status, _ = server.append('Sent', '(\\Seen)', imaplib.Time2Internaldate(time.time()), message.as_bytes())
        assert status == 'OK'
    finally:
        server.logout()


def test_mail_of_a_user_who_is_later_removed(app_domain, domain, device):
    send_as(app_domain, domain, REMOVED_USER, 'migrated-{0}-orphan'.format(REMOVED_USER))
    retry_func(lambda: assert_count(app_domain, REMOVED_USER, 'INBOX', 1), message='delivery to removed user',
               retries=30, sleep=3)
    output = device.run_ssh('snap run platform.cli user remove {0}'.format(REMOVED_USER))
    assert 'removed' in output, output
    device.run_ssh('ls /var/snap/mail/current/box/{0}'.format(REMOVED_USER))


def test_record_counts(app_domain):
    counts = {user: folder_counts(app_domain, user) for user in USERS.keys()}
    print(counts)
    with open(COUNTS_FILE, 'w') as f:
        json.dump(counts, f)


def password(user):
    return USERS.get(user, REMOVED_PASSWORD)


def send_as(app_domain, domain, user, subject):
    server = smtplib.SMTP(app_domain, 587, timeout=10)
    server.ehlo()
    server.login(user, password(user))
    message = MIMEText('body of {0}'.format(subject))
    message['Subject'] = subject
    message['From'] = '{0}@{1}'.format(user, domain)
    message['To'] = '{0}@{1}'.format(user, domain)
    server.send_message(message)
    server.quit()


def imap(app_domain, user):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    server = imaplib.IMAP4_SSL(app_domain, ssl_context=context)
    server.login(user, password(user))
    return server


def folder_counts(app_domain, user):
    server = imap(app_domain, user)
    try:
        counts = {}
        _, folders = server.list()
        for line in folders:
            name = LIST_LINE.match(line.decode()).group('name').strip('"')
            status, data = server.select('"{0}"'.format(name), readonly=True)
            if status == 'OK':
                counts[name] = int(data[0])
        return counts
    finally:
        server.logout()


def only(server, subject):
    _, data = server.search(None, 'SUBJECT', '"{0}"'.format(subject))
    ids = data[0].split()
    assert len(ids) == 1, '{0}: {1}'.format(subject, ids)
    return ids[0]


def assert_count(app_domain, user, folder, expected):
    server = imap(app_domain, user)
    try:
        status, data = server.select(folder)
        assert status == 'OK', data
        assert int(data[0]) == expected, '{0} {1}: {2}'.format(user, folder, data)
    finally:
        server.logout()
