import json
from os.path import dirname
from subprocess import check_output

import pytest
import requests
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install
from syncloudlib.integration.ssh import run_scp

from test.util.helper import retry_func
from test.util.mailbox import Mailbox

TMP_DIR = '/tmp/syncloud'
DIR = dirname(__file__)
USER = 'dave'
PASSWORD = 'Dave-Password1'
CONTACT = 'Erin Upgrade'
ADMIN_SOCKET = '/var/snap/mail/current/stalwart/admin.sock'
PUBLIC_SOCKET = '/var/snap/mail/current/stalwart.sock'
TUNNEL_SOCKET = '/var/snap/mail/current/spool/public/tunnel'
LISTENER_GET = '/tmp/listener-get.json'
STALWART_ENV = '/var/snap/mail/current/config/stalwart/stalwart.env'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('journalctl -u snap.mail.stalwart > {0}/upgrade.stalwart.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.bulwark > {0}/upgrade.bulwark.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/upgrade.*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


@pytest.fixture(scope="session")
def mailbox(app_domain, domain):
    return Mailbox(app_domain, domain, USER, PASSWORD)


def test_start(module_setup, app, device_host, domain, device):
    add_host_alias(app, device_host, domain)
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)


def test_install_released(device):
    device.run_ssh('snap remove mail')
    device.run_ssh('snap install mail', retries=3)
    assert 'stalwart' in device.run_ssh('snap services mail')


def test_add_user(device):
    output = device.run_ssh('snap run platform.cli user add {0} --password {1} --email {0}@external.example'.format(
        USER, PASSWORD))
    assert 'added' in output, output


def test_seed_mail(mailbox):
    for subject in ['upgrade-inbox', 'upgrade-project', 'upgrade-unread']:
        retry_func(lambda: mailbox.send(subject), message='send ' + subject, retries=10, sleep=5)
    retry_func(lambda: assert_equal(mailbox.count('INBOX'), 3), message='delivery', retries=30, sleep=3)


def test_seed_folder_and_flags(mailbox):
    server = mailbox.imap()
    try:
        assert server.create('Projects')[0] == 'OK'
        server.select('INBOX')
        _, data = server.search(None, 'SUBJECT', '"upgrade-project"')
        assert server.copy(data[0].split()[0], 'Projects')[0] == 'OK'
        _, data = server.search(None, 'SUBJECT', '"upgrade-inbox"')
        assert server.store(data[0].split()[0], '+FLAGS', '(\\Flagged \\Seen)')[0] == 'OK'
    finally:
        server.logout()


def test_seed_contact(app_domain, domain):
    response = requests.put(
        'https://{0}/dav/card/{1}@{2}/default/upgrade-contact.vcf'.format(app_domain, USER, domain),
        verify=False, auth=(USER, PASSWORD), headers={'Content-Type': 'text/vcard'},
        data='BEGIN:VCARD\r\nVERSION:3.0\r\nUID:upgrade-contact\r\nFN:{0}\r\nN:Upgrade;Erin;;;\r\n'
             'EMAIL:erin@example.com\r\nEND:VCARD\r\n'.format(CONTACT))
    assert response.status_code in (201, 204), response.text


def test_upgrade(device, device_password, device_host, app_archive_path):
    local_install(device_host, device_password, app_archive_path)
    assert 'stalwart' in device.run_ssh('snap services mail')


def test_mail_survived(mailbox):
    retry_func(lambda: assert_equal(mailbox.count('INBOX'), 3), message='inbox after upgrade', retries=20, sleep=3)
    assert mailbox.count('Projects') == 1


def test_flags_survived(mailbox):
    flags = mailbox.flags('INBOX', 'upgrade-inbox')
    assert '\\Flagged' in flags and '\\Seen' in flags, flags
    assert '\\Seen' not in mailbox.flags('INBOX', 'upgrade-unread')


def test_contact_survived(app_domain, domain):
    response = requests.request(
        'PROPFIND', 'https://{0}/dav/card/{1}@{2}/default/'.format(app_domain, USER, domain),
        verify=False, auth=(USER, PASSWORD), headers={'Depth': '1'},
        data='<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">'
             '<d:prop><c:address-data/></d:prop></d:propfind>')
    assert response.status_code == 207, response.text
    assert CONTACT in response.text, response.text


def test_listeners_moved_to_unix_bind_entries(device, device_host):
    run_scp('{0}/jmap/listener-get.json root@{1}:{2}'.format(DIR, device_host, LISTENER_GET),
            password=device.ssh_password)
    response = device.run_ssh('curl -s --unix-socket {0} -H Content-Type:application/json -d @{1} http://localhost/jmap/'.format(
        ADMIN_SOCKET, LISTENER_GET))
    listeners = {listener['name']: list(listener['bind']) for listener in json.loads(response)['methodResponses'][0][1]['list']}
    assert listeners['http'] == ['unix:{0}:443'.format(PUBLIC_SOCKET)], response
    assert listeners['tunnel'] == ['unix:{0}:25'.format(TUNNEL_SOCKET)], response


def test_unix_listener_variable_is_gone(device):
    assert 'STALWART_UNIX_LISTENERS' not in device.run_ssh('cat {0}'.format(STALWART_ENV))


def assert_equal(actual, expected):
    assert actual == expected, actual
