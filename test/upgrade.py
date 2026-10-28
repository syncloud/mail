import imaplib
import json
import ssl
from subprocess import check_output

import pytest
import requests
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install

from test.upgrade_prev import USERS, REMOVED_USER, COUNTS_FILE, LIST_LINE
from test.util.helper import retry_func

TMP_DIR = '/tmp/syncloud'
MIGRATION_DONE = '/var/snap/mail/current/migration/done'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('journalctl > {0}/upgrade.journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.migrate > {0}/upgrade.migrate.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.stalwart > {0}/upgrade.stalwart.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/mail/current/migration > {0}/upgrade.migration.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/upgrade.*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain, device):
    add_host_alias(app, device_host, domain)
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)


def test_old_stack_is_installed(device):
    assert 'dovecot' in device.run_ssh('snap services mail')


def test_upgrade(device, device_password, device_host, app_archive_path):
    local_install(device_host, device_password, app_archive_path)
    assert 'stalwart' in device.run_ssh('snap services mail')


def test_migration_finishes(device):
    retry_func(lambda: device.run_ssh('test -f {0}'.format(MIGRATION_DONE)), message='migration', retries=60, sleep=5)


@pytest.mark.parametrize('user', USERS.keys())
def test_inbox_survived_with_flags(app_domain, user):
    server = imap(app_domain, user)
    try:
        status, data = server.select('INBOX')
        assert status == 'OK', data
        _, found = server.search(None, 'SUBJECT', '"migrated-{0}-inbox"'.format(user))
        ids = found[0].split()
        assert len(ids) == 1, ids
        _, flags = server.fetch(ids[0], '(FLAGS)')
        assert b'\\Flagged' in flags[0], flags
        assert b'\\Seen' in flags[0], flags
        _, found = server.search(None, 'SUBJECT', '"migrated-{0}-project"'.format(user))
        assert found[0].split() == [], 'the project mail was moved out of the inbox before the upgrade'
    finally:
        server.logout()


@pytest.mark.parametrize('user', USERS.keys())
def test_folder_survived(app_domain, user):
    server = imap(app_domain, user)
    try:
        status, data = server.select('Projects')
        assert status == 'OK', data
        _, found = server.search(None, 'SUBJECT', '"migrated-{0}-project"'.format(user))
        assert len(found[0].split()) == 1, found
    finally:
        server.logout()


ROLES = {'Sent': '\\Sent', 'Drafts': '\\Drafts', 'Trash': '\\Trash', 'Junk': '\\Junk'}


@pytest.mark.parametrize('user', USERS.keys())
def test_every_folder_kept_its_messages(app_domain, user):
    with open(COUNTS_FILE) as f:
        before = json.load(f)[user]
    server = imap(app_domain, user)
    try:
        _, listed = server.list()
        folders = [LIST_LINE.match(line.decode()) for line in listed]
        by_role = {flag: match.group('name').strip('"') for match in folders for flag in match.group('flags').split()}
        after = {}
        for name in before:
            target = by_role[ROLES[name]] if name in ROLES else name
            status, data = server.select('"{0}"'.format(target), readonly=True)
            assert status == 'OK', '{0} -> {1}: {2}'.format(name, target, data)
            after[name] = int(data[0])
    finally:
        server.logout()
    assert after == before


@pytest.mark.parametrize('user', USERS.keys())
def test_unread_stays_unread(app_domain, user):
    server = imap(app_domain, user)
    try:
        server.select('INBOX', readonly=True)
        _, found = server.search(None, 'SUBJECT', '"migrated-{0}-unread"'.format(user))
        ids = found[0].split()
        assert len(ids) == 1, ids
        _, flags = server.fetch(ids[0], '(FLAGS)')
        assert b'\\Seen' not in flags[0], flags
    finally:
        server.logout()


@pytest.mark.parametrize('user', USERS.keys())
def test_sent_mail_is_in_the_sent_folder(app_domain, user):
    server = imap(app_domain, user)
    try:
        _, listed = server.list()
        sent = [m.group('name').strip('"') for m in (LIST_LINE.match(line.decode()) for line in listed)
                if '\\Sent' in m.group('flags').split()]
        assert len(sent) == 1, listed
        server.select('"{0}"'.format(sent[0]), readonly=True)
        _, found = server.search(None, 'SUBJECT', '"migrated-{0}-sent"'.format(user))
        assert len(found[0].split()) == 1, found
    finally:
        server.logout()


def test_mailbox_without_a_user_is_skipped_and_kept(device):
    device.run_ssh('test -f /var/snap/mail/current/migration/{0}.skipped'.format(REMOVED_USER))
    device.run_ssh('ls /var/snap/mail/current/box/{0}/cur'.format(REMOVED_USER))


def test_contact_survived(app_domain, domain):
    response = requests.request(
        'PROPFIND', 'https://{0}/dav/card/alice@{1}/default/'.format(app_domain, domain),
        verify=False, auth=('alice', USERS['alice']), headers={'Depth': '1'},
        data='<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">'
             '<d:prop><c:address-data/></d:prop></d:propfind>')
    assert response.status_code == 207, response.text
    assert 'Carol Contact' in response.text, response.text


def test_migration_is_not_repeated(device):
    device.run_ssh('snap restart mail.migrate')
    log = device.run_ssh('journalctl -u snap.mail.migrate --since "1 min ago" --no-pager', throw=False)
    assert 'imported mail' not in log, log


def imap(app_domain, user):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    server = imaplib.IMAP4_SSL(app_domain, ssl_context=context)
    server.login(user, USERS[user])
    return server
